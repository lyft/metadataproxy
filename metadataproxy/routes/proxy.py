from flask import Response
from flask import request
from flask import stream_with_context
from flask import jsonify

import requests

from metadataproxy import app
from metadataproxy import log
from metadataproxy import roles


def _supports_iam(version):
    '''Check the meta-data version for IAM support

    API versions before 2012-01-12 don't support the iam/ subtree.
    This function works because:
    >>> '1.0' < '2007-01-19' < '2014-11-05' < 'latest'
    True
    '''
    return version >= '2012-01-12'


@app.route('/<api_version>/meta-data/iam/info', strict_slashes=False)
@app.route('/<api_version>/meta-data/iam/info/<path:junk>')
def iam_role_info(api_version, junk=None):
    if not _supports_iam(api_version):
        return passthrough(request.path)

    role_name_from_ip = roles.get_role_name_from_ip(request.remote_addr)
    if role_name_from_ip:
        log.debug('Providing IAM role info for {0}'.format(role_name_from_ip))
        return jsonify(roles.get_role_info_from_ip(request.remote_addr))
    else:
        log.error('Role name not found; returning 404.')
        return '', 404


@app.route('/<api_version>/meta-data/iam/security-credentials/')
def iam_role_name(api_version):
    if not _supports_iam(api_version):
        return passthrough(request.path)

    role_name_from_ip = roles.get_role_name_from_ip(request.remote_addr)
    if role_name_from_ip:
        return role_name_from_ip
    else:
        log.error('Role name not found; returning 404.')
        return '', 404


@app.route('/<api_version>/meta-data/iam/security-credentials/<requested_role>',
           strict_slashes=False)
@app.route('/<api_version>/meta-data/iam/security-credentials/<requested_role>/<path:junk>')
def iam_sts_credentials(api_version, requested_role, junk=None):
    if not _supports_iam(api_version):
        return passthrough(request.path)

    if not roles.check_role_name_from_ip(request.remote_addr, requested_role):
        msg = "Role name {0} doesn't match expected role for container"
        log.error(msg.format(requested_role))
        return '', 404
    role_name = roles.get_role_name_from_ip(
        request.remote_addr,
        stripped=False
    )
    log.debug('Providing assumed role credentials for {0}'.format(role_name))
    assumed_role = roles.get_assumed_role_credentials(
        requested_role=role_name,
        api_version=api_version
    )
    return jsonify(assumed_role)


@app.route('/<path:url>')
@app.route('/')
def passthrough(url=''):
    log.debug('Did not match credentials request url; passing through.')
    req = requests.get(
        '{0}/{1}'.format(app.config['METADATA_URL'], url),
        stream=True
    )
    return Response(
        stream_with_context(req.iter_content()),
        content_type=req.headers['content-type']
    )
