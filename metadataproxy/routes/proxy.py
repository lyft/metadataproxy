import logging

import requests
from flask import Response
from flask import request
from flask import stream_with_context
from flask import jsonify

from metadataproxy import app
from metadataproxy import roles

log = logging.getLogger(__name__)


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

    role_params_from_ip = roles.get_role_params_from_ip(request.remote_addr)
    if role_params_from_ip['name']:
        log.debug('Providing IAM role info for {0}'.format(role_params_from_ip['name']))
        return jsonify(roles.get_role_info_from_params(role_params_from_ip))
    else:
        log.error('Role name not found; returning 404.')
        return '', 404


@app.route('/<api_version>/meta-data/iam/security-credentials/')
def iam_role_name(api_version):
    if not _supports_iam(api_version):
        return passthrough(request.path)

    role_params_from_ip = roles.get_role_params_from_ip(request.remote_addr)
    if role_params_from_ip['name']:
        return role_params_from_ip['name']
    else:
        log.error('Role name not found; returning 404.')
        return '', 404


@app.route('/<api_version>/meta-data/iam/security-credentials/<path:requested_role>',
           strict_slashes=False)
def iam_sts_credentials(api_version, requested_role):
    if not _supports_iam(api_version):
        return passthrough(request.path)

    try:
        role_params = roles.get_role_params_from_ip(
            request.remote_addr,
            requested_role=requested_role.rstrip('/')
        )
    except roles.UnexpectedRoleError:
        msg = "Role name {0} doesn't match expected role for container"
        log.error(msg.format(requested_role))
        return '', 404

    log.debug('Providing assumed role credentials for {0}'.format(role_params['name']))
    assumed_role = roles.get_assumed_role_credentials(
        role_params=role_params,
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
        content_type=req.headers['content-type'],
        status=req.status_code
    )
