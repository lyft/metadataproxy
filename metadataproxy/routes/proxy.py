import requests

from flask import Blueprint
from flask import jsonify
from flask import request
from flask import Response
from flask import stream_with_context

from metadataproxy import roles
from metadataproxy.log import get_logger
from metadataproxy.log import log_request
from metadataproxy.settings import Settings


blueprint_http = Blueprint('proxy_blueprint_http', __name__)
logger = get_logger(__name__)
request_logger = get_logger('werkzeug')


def _supports_iam(version):
    '''Check the meta-data version for IAM support

    API versions before 2012-01-12 don't support the iam/ subtree.
    This function works because:
    >>> '1.0' < '2007-01-19' < '2014-11-05' < 'latest'
    True
    '''
    return version >= '2012-01-12'


@blueprint_http.after_request
def log_http_request(response):
    log_request(request, response, request_logger)
    return response


@blueprint_http.route('/<api_version>/meta-data/iam/info', strict_slashes=False)
@blueprint_http.route('/<api_version>/meta-data/iam/info/<path:junk>')
def iam_role_info(api_version, junk=None):
    if not _supports_iam(api_version):
        return passthrough(request.path)

    role_name_from_ip = roles.get_role_name_from_ip(request.remote_addr)
    if role_name_from_ip:
        logger.debug('Providing IAM role info for {0}'.format(role_name_from_ip))
        return jsonify(roles.get_role_info_from_ip(request.remote_addr))
    else:
        logger.error('Role name not found; returning 404.')
        return '', 404


@blueprint_http.route('/<api_version>/meta-data/iam/security-credentials/')
def iam_role_name(api_version):
    if not _supports_iam(api_version):
        return passthrough(request.path)

    role_name_from_ip = roles.get_role_name_from_ip(request.remote_addr)
    if role_name_from_ip:
        return role_name_from_ip
    else:
        logger.error('Role name not found; returning 404.')
        return '', 404


@blueprint_http.route('/<api_version>/meta-data/iam/security-credentials/<requested_role>',
                      strict_slashes=False)
@blueprint_http.route('/<api_version>/meta-data/iam/security-credentials/<requested_role>/<path:junk>')
def iam_sts_credentials(api_version, requested_role, junk=None):
    if not _supports_iam(api_version):
        return passthrough(request.path)

    if not roles.check_role_name_from_ip(request.remote_addr, requested_role):
        msg = "Role name {0} doesn't match expected role for container"
        logger.error(msg.format(requested_role))
        return '', 404
    role_name = roles.get_role_name_from_ip(
        request.remote_addr,
        stripped=False
    )
    logger.debug('Providing assumed role credentials for {0}'.format(role_name))
    assumed_role = roles.get_assumed_role_credentials(
        requested_role=role_name,
        api_version=api_version
    )
    return jsonify(assumed_role)


@blueprint_http.route('/<path:url>')
@blueprint_http.route('/')
def passthrough(url=''):
    logger.debug('Did not match credentials request url; passing through.')
    req = requests.get(
        '{0}/{1}'.format(Settings.METADATA_URL, url),
        stream=True
    )
    return Response(
        stream_with_context(req.iter_content()),
        content_type=req.headers['content-type']
    )
