import json
from os import getenv


def bool_env(var_name, default=False):
    """
    Get an environment variable coerced to a boolean value.
    Example:
        Bash:
            $ export SOME_VAL=True
        settings.py:
            SOME_VAL = bool_env('SOME_VAL', False)
    Arguments:
        var_name: The name of the environment variable.
        default: The default to use if `var_name` is not specified in the
                 environment.
    Returns: `var_name` or `default` coerced to a boolean using the following
        rules:
            "False", "false" or "" => False
            Any other non-empty string => True
    """
    test_val = getenv(var_name, default)
    # Explicitly check for 'False', 'false', and '0' since all non-empty
    # string are normally coerced to True.
    if test_val in ('False', 'false', '0'):
        return False
    return bool(test_val)


def float_env(var_name, default=0.0):
    """
    Get an environment variable coerced to a float value.
    This has the same arguments as bool_env. If a value cannot be coerced to a
    float, a ValueError will be raised.
    """
    return float(getenv(var_name, default))


def int_env(var_name, default=0):
    """
    Get an environment variable coerced to an integer value.
    This has the same arguments as bool_env. If a value cannot be coerced to an
    integer, a ValueError will be raised.
    """
    return int(getenv(var_name, default))


def str_env(var_name, default=''):
    """
    Get an environment variable as a string.
    This has the same arguments as bool_env.
    """
    return getenv(var_name, default)


PORT = int_env('PORT', 45001)
HOST = str_env('HOST', '0.0.0.0')
DEBUG = bool_env('DEBUG', False)

# Url of the docker daemon. The default is to access docker via its socket.
DOCKER_URL = str_env('DOCKER_URL', 'unix://var/run/docker.sock')
# URL of the metadata service. Default is the normal location of the
# metadata service in AWS.
METADATA_URL = str_env('METADATA_URL', 'http://169.254.169.254')
# Whether or not to mock all metadata endpoints. If True, mocked data will be
# returned to callers. If False, all endpoints except for IAM endpoints will be
# proxied through to the real metadata service.
MOCK_API = bool_env('MOCK_API', False)
# When mocking the API, use the following instance id in returned data.
MOCKED_INSTANCE_ID = str_env('MOCKED_INSTANCE_ID', 'mockedid')

# Role to use if IAM_ROLE is not set in a container's environment. If unset
# the container will get no IAM credentials.
DEFAULT_ROLE = str_env('DEFAULT_ROLE')
# The default account ID to assume roles in, if IAM_ROLE does not contain
# account information. If unset, metadataproxy will attempt to lookup role
# ARNs using IAM:GET_ROLE, if the IAM_ROLE name is not an ARN.
DEFAULT_ACCOUNT_ID = str_env('DEFAULT_ACCOUNT_ID')
# A mapping of account names to account IDs. This allows you to use
# user-friendly names in the IAM_ROLE environment variable; for instance:
#
#   AWS_ACCOUNT_MAP={'my-account-name':'12345'}
#
# A lookup of myrole@my-account-name would map to
#
#   role_name: myrole
#   account_id: 12345
AWS_ACCOUNT_MAP = json.loads(str_env('AWS_ACCOUNT_MAP', '{}'))

# A json file that has a dict mapping of IP addresses to role names. Can be
# used if docker networking has been disabled and you are managing IP
# addressing for containers through another process.
ROLE_MAPPING_FILE = str_env('ROLE_MAPPING_FILE')
# Do a reverse lookup of incoming IP addresses to match containers by hostname.
# Useful if you've disabled networking in docker, but set hostnames for
# containers in /etc/hosts or DNS.
ROLE_REVERSE_LOOKUP = bool_env('ROLE_REVERSE_LOOKUP', False)
# Limit reverse lookup container matching to hostnames that match the specified
# pattern.
HOSTNAME_MATCH_REGEX = str_env('HOSTNAME_MATCH_REGEX', '^.*$')
# Optional key in container labels or environment variables to use for role session name.
# Prefix with Labels: or Env: respectively to indicate where key should be found.
ROLE_SESSION_KEY = str_env('ROLE_SESSION_KEY')
