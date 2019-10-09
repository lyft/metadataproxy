import datetime
import dateutil
import logging

from flask import request
from flask import redirect
from flask import url_for
from flask import jsonify

from metadataproxy import app
from metadataproxy import roles

log = logging.getLogger(__name__)


@app.route(
    '/<api_version>'
)
def root_noslash(api_version):
    return redirect(
        url_for('root_slash', api_version=api_version),
        code=301
    )


@app.route(
    '/<api_version>/'
)
def root_slash(api_version):
    return 'meta-data', 200


@app.route(
    '/<api_version>/meta-data'
)
def get_meta_data_noslash(api_version):
    return redirect(
        url_for('get_meta_data_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/meta-data/')
def get_meta_data_slash(api_version):
    meta_data_list = [
        'ami-id', 'ami-launch-index', 'ami-manifest-path',
        'block-device-mapping/', 'hostname', 'iam/', 'instance-action',
        'instance-id', 'instance-type', 'local-hostname', 'local-ipv4',
        'mac', 'metrics/', 'network/', 'placement/', 'profile',
        'public-hostname', 'public-ipv4', 'public-keys/', 'reservation-id',
        'security-groups', 'services/'
    ]
    return '\n'.join(meta_data_list), 200


@app.route('/<api_version>/meta-data/ami-id')
def get_ami_id(api_version):
    return 'ami-mockedami', 200


@app.route('/<api_version>/meta-data/ami-launch-index')
def get_ami_launch_index(api_version):
    return '0', 200


@app.route('/<api_version>/meta-data/ami-manifest-path')
def get_ami_manifest_path(api_version):
    return '(unknown)', 200


@app.route('/<api_version>/meta-data/block-device-mapping')
def get_block_device_mapping_noslash(api_version):
    return redirect(
        url_for('get_block_device_mapping_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/meta-data/block-device-mapping/')
def get_block_device_mapping_slash(api_version):
    return 'ami\nroot', 200


@app.route('/<api_version>/meta-data/block-device-mapping/ami')
def get_block_device_mapping_ami(api_version):
    return '/dev/sda1', 200


@app.route('/<api_version>/meta-data/block-device-mapping/root')
def get_block_device_mapping_root(api_version):
    return '/dev/sda1', 200


@app.route('/<api_version>/meta-data/hostname')
def get_hostname(api_version):
    return 'mocked.internal', 200


@app.route('/<api_version>/meta-data/iam')
def get_iam_noslash(api_version):
    return redirect(
        url_for('get_iam_slash', api_version=api_version),
        301
    )


@app.route('/<api_version>/meta-data/iam/')
def get_iam_slash(api_version):
    return 'info\nsecurity-credentials/', 200


@app.route('/<api_version>/meta-data/iam/info', strict_slashes=False)
@app.route('/<api_version>/meta-data/iam/info/<path:junk>')
def get_iam_info(api_version, junk=None):
    role_params_from_ip = roles.get_role_params_from_ip(request.remote_addr)
    if role_params_from_ip['name']:
        log.debug('Providing IAM role info for {0}'.format(role_params_from_ip['name']))
        return jsonify(roles.get_role_info_from_params(role_params_from_ip))
    else:
        log.error('Role name not found; returning 404.')
        return '', 404


@app.route('/<api_version>/meta-data/iam/security-credentials')
def get_security_credentials_noslash(api_version):
    return redirect(
        url_for('get_security_credentials_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/meta-data/iam/security-credentials/')
def get_security_credentials_slash(api_version):
    role_params = roles.get_role_params_from_ip(request.remote_addr)
    if not role_params['name']:
        return '', 404
    return role_params['name'], 200


@app.route(
    '/<api_version>/meta-data/iam/security-credentials/<requested_role>',
    methods=['GET'],
    strict_slashes=False
)
@app.route(
    '/<api_version>/meta-data/iam/security-credentials/<requested_role>/<path:junk>',
    methods=['GET']
)
def get_role_credentials(api_version, requested_role, junk=None):
    try:
        role_params = roles.get_role_params_from_ip(
            request.remote_addr,
            requested_role=requested_role
        )
    except roles.UnexpectedRoleError:
        return '', 403

    try:
        assumed_role = roles.get_assumed_role_credentials(
            role_params=role_params,
            api_version=api_version
        )
    except roles.GetRoleError as e:
        return '', e.args[0][0]
    return jsonify(assumed_role)


@app.route('/<api_version>/meta-data/instance-action')
def get_instance_action(api_version):
    return 'none', 200


@app.route('/<api_version>/meta-data/instance-id')
def get_instance_id(api_version):
    return 'i-{0}'.format(app.config['MOCKED_INSTANCE_ID']), 200


@app.route('/<api_version>/meta-data/instance-type')
def get_instance_type(api_version):
    return 't2.medium', 200


@app.route('/<api_version>/meta-data/mac')
def get_mac(api_version):
    return 'AE-30-76-CE-38-62', 200


@app.route('/<api_version>/meta-data/metrics')
def get_metrics_noslash(api_version):
    return redirect(
        url_for('get_metrics_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/meta-data/metrics/')
def get_metrics_slash(api_version):
    return 'vhostmd', 200


@app.route('/<api_version>/meta-data/metrics/vhostmd')
def get_metrics_vhostmd(api_version):
    return '<?xml version="1.0" encoding="UTF-8"?>', 200


@app.route('/<api_version>/meta-data/network')
def get_network_noslash(api_version):
    return redirect(
        url_for('get_network_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/meta-data/network/')
def get_network_slash(api_version):
    return 'interfaces/', 200


@app.route('/<api_version>/meta-data/network/interfaces')
def get_network_interfaces_noslash(api_version):
    return redirect(
        url_for('get_network_interfaces_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/meta-data/network/interfaces/')
def get_network_interfaces_slash(api_version):
    return 'macs/', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs')
def get_network_interfaces_macs_noslash(api_version):
    return redirect(
        url_for('get_network_interfaces_macs_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/meta-data/network/interfaces/macs/')
def get_network_interfaces_macs_slash(api_version):
    return 'AE:30:76:CE:38:62/', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62')
def get_network_interfaces_macaddr_noslash(api_version):
    return redirect(
        url_for(
            'get_network_interfaces_macaddr_slash',
            api_version=api_version
        ),
        code=301
    )


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/')
def get_network_interfaces_macaddr_slash(api_version):
    info = [
        'device-number', 'interface-id', 'ipv4-associations/',
        'local-hostname', 'local-ipv4s', 'mac', 'owner-id', 'public-hostname',
        'public-ipv4s', 'security-group-ids', 'security-groups', 'subnet-id',
        'subnet-ipv4-cidr-block', 'vpc-id', 'vpc-ipv4-cidr-block'
    ]
    return '\n'.join(info), 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/device-number')
def get_macaddr_device_number(api_version):
    return '0', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/interface-id')
def get_macaddr_interface_id(api_version):
    return 'eni-1234', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/ipv4-associations')
def get_macaddr_ipv4_associations_noslash(api_version):
    return redirect(
        url_for(
            'get_macaddr_ipv4_associations_slash',
            api_version=api_version
        ),
        code=301
    )


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/ipv4-associations/')
def get_macaddr_ipv4_associations_slash(api_version):
    return '127.255.0.1', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/local-hostname')
def get_macaddr_local_hostname(api_version):
    return 'mocked.internal', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/local-ipv4s')
def get_macaddr_local_ipv4s(api_version):
    return 'mocked.internal', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/mac')
def get_macaddr_mac(api_version):
    return 'AE:30:76:CE:38:62', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/owner-id')
def get_macaddr_owner_id(api_version):
    return '12345', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/public-hostname')
def get_macaddr_public_hostname(api_version):
    return 'mocked.internal', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/public-ipv4s')
def get_macaddr_public_ipv4s(api_version):
    return '127.255.0.1', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/security-group-ids')
def get_macaddr_security_group_ids(api_version):
    return 'sg-1234', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/security-groups')
def get_macaddr_security_groups(api_version):
    return 'default', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/subnet-id')
def get_macaddr_subnet_id(api_version):
    return 'subnet-1234', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/subnet-ipv4-cidr-block')
def get_macaddr_subnet_ipv4_cidr_block(api_version):
    return '127.255.0.0/20', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/vpc-id')
def get_macaddr_vpc_id(api_version):
    return 'vpc-1234', 200


@app.route('/<api_version>/meta-data/network/interfaces/macs/AE:30:76:CE:38:62/vpc-ipv4-cidr-block')
def get_macaddr_vpc_ipv4_cidr_block(api_version):
    return '127.255.0.0/16', 200


@app.route('/<api_version>/meta-data/placement')
def get_placement_noslash(api_version):
    return redirect(
        url_for('get_placement_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/meta-data/placement/')
def get_placement_slash(api_version):
    return 'availability-zone', 200


@app.route('/<api_version>/meta-data/placement/availability-zone')
def get_placement_az(api_version):
    return 'us-east-1a', 200


@app.route('/<api_version>/meta-data/profile')
def get_profile(api_version):
    return 'default-hvm', 200


@app.route('/<api_version>/meta-data/public-hostname')
def get_public_hostname(api_version):
    return 'mocked.internal', 200


@app.route('/<api_version>/meta-data/public-ipv4')
def get_public_ipv4s(api_version):
    return '127.255.0.1', 200


@app.route('/<api_version>/meta-data/public-keys')
def get_public_keys_noslash(api_version):
    return redirect(
        url_for('get_public_keys_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/meta-data/public-keys/')
def get_public_keys_slash(api_version):
    return '0=boot', 200


@app.route('/<api_version>/meta-data/reservation-id')
def get_reservation_id(api_version):
    return 'r-1234', 200


@app.route('/<api_version>/meta-data/security-groups')
def get_security_groups(api_version):
    return 'default', 200


@app.route('/<api_version>/meta-data/services')
def get_services_noslash(api_version):
    return redirect(
        url_for('get_services_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/meta-data/services/')
def get_services_slash(api_version):
    return 'domain', 200


@app.route('/<api_version>/meta-data/services/domain')
def get_services_domain(api_version):
    return 'amazonaws.com', 200


@app.route('/<api_version>/dynamic')
def get_dynamic_noslash(api_version):
    return redirect(
        url_for('get_dynamic_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/dynamic/')
def get_dynamic_slash(api_version):
    return 'instance-identity/\nfws/\n', 200


@app.route('/<api_version>/dynamic/instance-identity')
def get_instance_identity_noslash(api_version):
    return redirect(
        url_for('get_instance_identity_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/dynamic/instance-identity/')
def get_instance_identity_slash(api_version):
    return 'document\npkcs7\nsignature\ndsa2048', 200


@app.route('/<api_version>/dynamic/instance-identity/document')
def get_instance_identity_document(api_version):
    time_format = "%Y-%m-%dT%H:%M:%SZ"
    now = datetime.datetime.now(dateutil.tz.tzutc())
    ret = {
        'privateIp': '127.255.0.1',
        'devpayProductCodes': None,
        'availabilityZone': 'us-east-1a',
        'version': '2010-08-31',
        'accountId': '1234',
        'instanceId': 'i-{0}'.format(app.config['MOCKED_INSTANCE_ID']),
        'billingProducts': None,
        'instanceType': 't2.medium',
        # This may be a terrible mock for this...
        'pendingTime': now.strftime(time_format),
        'imageId': 'ami-1234',
        'kernelId': None,
        'ramdiskId': None,
        'architecture': 'x86_64',
        'region': 'us-east-1'
    }
    return jsonify(ret)


@app.route('/<api_version>/dynamic/instance-identity/pkcs7')
def get_instance_identity_pkcs7(api_version):
    # TODO: determine a reasonable mock for this
    return 'mocked', 200


@app.route('/<api_version>/dynamic/instance-identity/signature')
def get_instance_identity_signature(api_version):
    # TODO: determine a reasonable mock for this
    return 'mocked', 200


@app.route('/<api_version>/dynamic/instance-identity/dsa2048')
def get_instance_identity_dsa2048(api_version):
    # TODO: determine a reasonable mock for this
    return 'mocked', 200


@app.route('/<api_version>/dynamic/fws')
def get_fws_noslash(api_version):
    return redirect(
        url_for('get_fws_slash', api_version=api_version),
        code=301
    )


@app.route('/<api_version>/dynamic/fws/')
def get_fws_slash(api_version):
    return 'instance-monitoring\n', 200


@app.route('/<api_version>/dynamic/fws/instance-monitoring')
def get_instance_monitoring(api_version):
    return 'enabled', 200
