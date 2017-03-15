# Import python libs
import datetime
import dateutil.tz
import json
import socket
import re
import timeit

# Import third party libs
import boto3
import docker
import docker.errors
from botocore.exceptions import ClientError

# Import metadataproxy libs
from metadataproxy import app
from metadataproxy import log

ROLES = {}
CONTAINER_MAPPING = {}
_docker_client = None
_iam_client = None
_sts_client = None

if app.config['ROLE_MAPPING_FILE']:
    with open(app.config.get('ROLE_MAPPING_FILE'), 'r') as f:
        ROLE_MAPPINGS = json.loads(f.read())
else:
    ROLE_MAPPINGS = {}

RE_IAM_ARN = re.compile(r"arn:aws:iam::(\d+):role/(.*)")


class BlockTimer(object):
    def __enter__(self):
        self.start_time = timeit.default_timer()
        return self

    def __exit__(self, *args):
        self.end_time = timeit.default_timer()
        self.exec_duration = self.end_time - self.start_time


class PrintingBlockTimer(BlockTimer):
    def __init__(self, prefix=''):
        self.prefix = prefix

    def __exit__(self, *args):
        super(PrintingBlockTimer, self).__exit__(*args)
        msg = "Execution took {0:f}s".format(self.exec_duration)
        if self.prefix:
            msg = self.prefix + ': ' + msg
        log.debug(msg)


def log_exec_time(method):
    def timed(*args, **kw):
        with PrintingBlockTimer(method.__name__):
            result = method(*args, **kw)
        return result
    return timed


def docker_client():
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.Client(base_url=app.config['DOCKER_URL'])
    return _docker_client


def iam_client():
    global _iam_client
    if _iam_client is None:
        _iam_client = boto3.client('iam')
    return _iam_client


def sts_client():
    global _sts_client
    if _sts_client is None:
        _sts_client = boto3.client('sts')
    return _sts_client


@log_exec_time
def find_container(ip):
    pattern = re.compile(app.config['HOSTNAME_MATCH_REGEX'])
    client = docker_client()
    # Try looking at the container mapping cache first
    if ip in CONTAINER_MAPPING:
        log.info('Container id for IP {0} in cache'.format(ip))
        try:
            with PrintingBlockTimer('Container inspect'):
                container = client.inspect_container(CONTAINER_MAPPING[ip])
            # Only return a cached container if it is running.
            if container['State']['Running']:
                return container
            else:
                log.error('Container id {0} is no longger running'.format(ip))
                del CONTAINER_MAPPING[ip]
        except docker.errors.NotFound:
            msg = 'Container id {0} no longer mapped to {1}'
            log.error(msg.format(CONTAINER_MAPPING[ip], ip))
            del CONTAINER_MAPPING[ip]

    _fqdn = None
    with PrintingBlockTimer('Reverse DNS'):
        if app.config['ROLE_REVERSE_LOOKUP']:
            try:
                _fqdn = socket.gethostbyaddr(ip)[0]
            except socket.error as e:
                log.error('gethostbyaddr failed: {0}'.format(e.args))
                pass

    with PrintingBlockTimer('Container fetch'):
        _ids = [c['Id'] for c in client.containers()]

    for _id in _ids:
        try:
            with PrintingBlockTimer('Container inspect'):
                c = client.inspect_container(_id)
        except docker.errors.NotFound:
            log.error('Container id {0} not found'.format(_id))
            continue
        # Try matching container to caller by IP address
        _ip = c['NetworkSettings']['IPAddress']
        if ip == _ip:
            msg = 'Container id {0} mapped to {1} by IP match'
            log.debug(msg.format(_id, ip))
            CONTAINER_MAPPING[ip] = _id
            return c
        # Try matching container to caller by sub network IP address
        _networks = c['NetworkSettings']['Networks']
        if _networks:
            for _network in _networks:
                if _networks[_network]['IPAddress'] == ip:
                    msg = 'Container id {0} mapped to {1} by sub-network IP match'
                    log.debug(msg.format(_id, ip))
                    CONTAINER_MAPPING[ip] = _id
                    return c
        # Try matching container to caller by hostname match
        if app.config['ROLE_REVERSE_LOOKUP']:
            hostname = c['Config']['Hostname']
            domain = c['Config']['Domainname']
            fqdn = '{0}.{1}'.format(hostname, domain)
            # Default pattern matches _fqdn == fqdn
            _groups = re.match(pattern, _fqdn).groups()
            groups = re.match(pattern, fqdn).groups()
            if _groups and groups:
                if groups[0] == _groups[0]:
                    msg = 'Container id {0} mapped to {1} by FQDN match'
                    log.debug(msg.format(_id, ip))
                    CONTAINER_MAPPING[ip] = _id
                    return c

    log.error('No container found for ip {0}'.format(ip))
    return None


def check_role_name_from_ip(ip, requested_role):
    role_name = get_role_name_from_ip(ip)
    if role_name == requested_role:
        log.debug('Detected Role: {0}, Requested Role: {1}'.format(
            role_name, requested_role
        ))
        return True
    return False


@log_exec_time
def get_role_name_from_ip(ip, stripped=True):
    if app.config['ROLE_MAPPING_FILE']:
        return ROLE_MAPPINGS.get(ip, app.config['DEFAULT_ROLE'])
    container = find_container(ip)
    if container:
        env = container['Config']['Env']
        for e in env:
            key, val = e.split('=', 1)
            if key == 'IAM_ROLE':
                if val.startswith('arn:aws'):
                    m = RE_IAM_ARN.match(val)
                    val = '{0}@{1}'.format(m.group(2), m.group(1))
                if stripped:
                    return val.split('@')[0]
                else:
                    return val
        msg = "Couldn't find IAM_ROLE variable. Returning DEFAULT_ROLE: {0}"
        log.debug(msg.format(app.config['DEFAULT_ROLE']))
        if stripped:
            return app.config['DEFAULT_ROLE'].split('@')[0]
        else:
            return app.config['DEFAULT_ROLE']
    else:
        return None


@log_exec_time
def get_role_info_from_ip(ip):
    role_name = get_role_name_from_ip(ip, stripped=False)
    if not role_name:
        return {}
    try:
        role = get_assumed_role(role_name)
    except GetRoleError:
        return {}
    time_format = "%Y-%m-%dT%H:%M:%SZ"
    now = datetime.datetime.now(dateutil.tz.tzutc())
    return {
        'Code': 'Success',
        # TODO: This is probably not the right thing to return here.
        'LastUpdated': now.strftime(time_format),
        'InstanceProfileArn': role['AssumedRoleUser']['Arn'],
        'InstanceProfileId': role['AssumedRoleUser']['AssumedRoleId']
    }


def get_role_arn(role_name):
    # Role name is an arn. Just return it.
    if role_name.startswith('arn:aws'):
        return role_name
    # Role name includes an account name/id, split them
    if '@' in role_name:
        assume_role, account_name = role_name.split('@')
    # No role name/id, try to get the default account id
    else:
        assume_role = role_name
        if app.config['DEFAULT_ACCOUNT_ID']:
            account_name = app.config['DEFAULT_ACCOUNT_ID']
        # No default account id defined. Get the ARN by looking up the role
        # name. This is a backwards compat use-case for when we didn't require
        # the default account id.
        else:
            iam = iam_client()
            try:
                with PrintingBlockTimer('iam.get_role'):
                    role = iam.get_role(RoleName=role_name)
                    return role['Role']['Arn']
            except ClientError as e:
                response = e.response['ResponseMetadata']
                raise GetRoleError((response['HTTPStatusCode'], e.message))
    # Map the name to an account ID. If it isn't found, assume an ID was passed
    # in and use that.
    account_id = app.config['AWS_ACCOUNT_MAP'].get(account_name, account_name)
    # Return a generated ARN
    return 'arn:aws:iam::{0}:role/{1}'.format(account_id, assume_role)


@log_exec_time
def get_assumed_role(requested_role):
    if requested_role in ROLES:
        assumed_role = ROLES[requested_role]
        expiration = assumed_role['Credentials']['Expiration']
        now = datetime.datetime.now(dateutil.tz.tzutc())
        expire_check = now + datetime.timedelta(minutes=5)
        if expire_check < expiration:
            return assumed_role
    arn = get_role_arn(requested_role)
    with PrintingBlockTimer('sts.assume_role'):
        sts = sts_client()
        assumed_role = sts.assume_role(
            RoleArn=arn,
            RoleSessionName='devproxyauth'
        )
    ROLES[requested_role] = assumed_role
    return assumed_role


@log_exec_time
def get_assumed_role_credentials(requested_role, api_version='latest'):
    assumed_role = get_assumed_role(requested_role)
    time_format = "%Y-%m-%dT%H:%M:%SZ"
    credentials = assumed_role['Credentials']
    expiration = credentials['Expiration']
    updated = expiration - datetime.timedelta(minutes=60)
    return {
        'Code': 'Success',
        'LastUpdated': updated.strftime(time_format),
        'Type': 'AWS-HMAC',
        'AccessKeyId': credentials['AccessKeyId'],
        'SecretAccessKey': credentials['SecretAccessKey'],
        'Token': credentials['SessionToken'],
        'Expiration': expiration.strftime(time_format)
    }


class GetRoleError(Exception):
    pass
