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
    container_id = CONTAINER_MAPPING.get(ip)
    if container_id:
        log.info('Container id for IP {0} in cache'.format(ip))
        try:
            with PrintingBlockTimer('Container inspect'):
                container = client.inspect_container(container_id)
            # Only return a cached container if it is running.
            if container['State']['Running']:
                return container
            else:
                log.error('Container id {0} is no longer running'.format(ip))
                if ip in CONTAINER_MAPPING:
                    del CONTAINER_MAPPING[ip]
        except docker.errors.NotFound:
            msg = 'Container id {0} no longer mapped to {1}'
            log.error(msg.format(container_id, ip))
            if ip in CONTAINER_MAPPING:
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
        # Not Found ? Let's see if we are running under rancher 1.2+,which uses a label to store the IP
        try:
            _labels = c.get('Config', {}).get('Labels', {})
        except (KeyError, ValueError):
            _labels = {}
        try:
            if _labels.get('io.rancher.container.ip'):
                _ip = _labels.get('io.rancher.container.ip').split("/")[0]
        except docker.errors.NotFound:
            log.error('Container: {0} Label container.ip not found'.format(_id))
        if ip == _ip:
            msg = 'Container id {0} mapped to {1} by Rancher IP match'
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


@log_exec_time
def get_role_params_from_ip(ip, requested_role=None):
    params = {'name': None, 'account_id': None, 'external_id': None, 'session_name': None}
    role_name = None
    if app.config['ROLE_MAPPING_FILE']:
        role = ROLE_MAPPINGS.get(ip, app.config['DEFAULT_ROLE'])
        if isinstance(role, dict):
            params.update(role)
        else:
            role_name = role
    else:
        container = find_container(ip)
        if container:
            env = container['Config']['Env'] or []
            # Look up IAM_ROLE and IAM_EXTERNAL_ID values from environment
            for e in env:
                key, val = e.split('=', 1)
                if key == 'IAM_ROLE':
                    if val.startswith('arn:aws'):
                        m = RE_IAM_ARN.match(val)
                        val = '{0}@{1}'.format(m.group(2), m.group(1))
                    role_name = val
                elif key == 'IAM_EXTERNAL_ID':
                    params['external_id'] = val
            if not role_name:
                msg = "Couldn't find IAM_ROLE variable. Returning DEFAULT_ROLE: {0}"
                log.debug(msg.format(app.config['DEFAULT_ROLE']))
                role_name = app.config['DEFAULT_ROLE']

            # Optionally, look up role session name from environment or labels
            if app.config['ROLE_SESSION_KEY']:
                skey = app.config['ROLE_SESSION_KEY']
                sval = None
                if skey.startswith('Env:'):
                    skey = skey[4:]
                    for e in env:
                        key, val = e.split('=', 1)
                        if skey == key:
                            sval = val
                elif skey.startswith('Labels:'):
                    skey = skey[7:]
                    if container['Config']['Labels'] and skey in container['Config']['Labels']:
                        sval = container['Config']['Labels'][skey]
                if sval and len(sval) > 1:
                    # The docs on RoleSessionName are slightly contradictory, and state:
                    # > The regex used to validate this parameter is a string of characters consisting
                    # > of upper- and lower-case alphanumeric characters with no spaces. You can also
                    # > include underscores or any of the following characters: =,.@-
                    # > Type: String
                    # > Length Constraints: Minimum length of 2. Maximum length of 64.
                    # > Pattern: [\w+=,.@-]*
                    # We replace any invalid chars with underscore, and trim to 64.
                    params['session_name'] = re.sub(r'[^\w+=,.@-]', '_', sval)[:64]
    if role_name:
        role_parts = role_name.split('@')
        params['name'] = role_parts[0]
        if len(role_parts) > 1:
            params['account_id'] = role_parts[1]

    if requested_role and requested_role != params['name']:
        raise UnexpectedRoleError

    return params


@log_exec_time
def get_role_info_from_params(role_params):
    if not role_params['name']:
        return {}
    try:
        role = get_assumed_role(role_params)
    except GetRoleError:
        return {}
    time_format = "%Y-%m-%dT%H:%M:%SZ"
    expiration = role['Credentials']['Expiration']
    updated = expiration - datetime.timedelta(minutes=60)
    return {
        'Code': 'Success',
        'LastUpdated': updated.strftime(time_format),
        'InstanceProfileArn': role['AssumedRoleUser']['Arn'],
        'InstanceProfileId': role['AssumedRoleUser']['AssumedRoleId']
    }


def get_role_arn(role_params):
    if role_params['account_id']:
        # Try to map the name to an account ID. If it isn't found, assume an ID was passed
        # in and use it as-is.
        role_params['account_id'] = app.config['AWS_ACCOUNT_MAP'].get(
            role_params['account_id'],
            role_params['account_id']
        )
    else:
        if app.config['DEFAULT_ACCOUNT_ID']:
            role_params['account_id'] = app.config['DEFAULT_ACCOUNT_ID']
        # No default account id defined. Get the ARN by looking up the role
        # name. This is a backwards compat use-case for when we didn't require
        # the default account id.
        else:
            iam = iam_client()
            try:
                with PrintingBlockTimer('iam.get_role'):
                    role = iam.get_role(RoleName=role_params['name'])
                    return role['Role']['Arn']
            except ClientError as e:
                response = e.response['ResponseMetadata']
                raise GetRoleError((response['HTTPStatusCode'], e.message))
    # Return a generated ARN
    return 'arn:aws:iam::{account_id}:role/{name}'.format(**role_params)


@log_exec_time
def get_assumed_role(role_params):
    arn = get_role_arn(role_params)
    if arn in ROLES:
        assumed_role = ROLES[arn]
        expiration = assumed_role['Credentials']['Expiration']
        now = datetime.datetime.now(dateutil.tz.tzutc())
        expire_check = now + datetime.timedelta(minutes=5)
        if expire_check < expiration:
            return assumed_role
    with PrintingBlockTimer('sts.assume_role'):
        sts = sts_client()
        session_name = role_params['session_name'] or 'devproxyauth'
        kwargs = {'RoleArn': arn, 'RoleSessionName': session_name}
        if role_params['external_id']:
            kwargs['ExternalId'] = role_params['external_id']
        assumed_role = sts.assume_role(**kwargs)
    ROLES[arn] = assumed_role
    return assumed_role


@log_exec_time
def get_assumed_role_credentials(role_params, api_version='latest'):
    assumed_role = get_assumed_role(role_params)
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


class UnexpectedRoleError(Exception):
    pass
