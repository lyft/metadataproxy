## 1.5.1

* Fix 500 error when retrieving role session name from Docker label

## 1.5.0

* New support retrieving container IP from Rancher labels

## 1.4.0

* Add IAM\_EXTERNAL\_ID variable: if found value will be populated into ExternalId parameter when making AssumeRole call.
* add ROLE\_SESSION\_KEY variable: if found will use value to look up key from Docker container labels or environment variable to set RoleSessionName when making AssumeRole call. See documentation for details.
* Reduce number of calls to Docker API when retrieving credentials.
* Bump WSGI dependency versions

## 1.3.2

* Packaging fixes for travis releases to docker hub

## 1.3.1

* Fix for k8s network lookup stacktrace

## 1.3.0

* Fix for reformatting IAM\_ROLE when it matches ARN format
* Add logging for when the expected role does not match the available role
* Export PYTHONUNBUFFERED in run-server.sh so logs come out as they are made available vs when python decides it's time
* Send log-file to stdout as well in run-server.sh

## 1.2.6

* In run-server.sh, sent stdout and stderr to stdout
* In run-server.sh, make the workers configurable
* In run-server.sh, use better bash syntax

## 1.2.5

* Add more package data to setup.py for sdist packing fix

## 1.2.4

* Add package data to setup.py for sdist packing fix

## 1.2.3

* Attempt to fix sdist packaging

## 1.2.2

* Attempt to fix sdist packaging

## 1.2.1

* Travis docker fix (packaging change)

## 1.2.0

* Look for container IP address in container's networks datastructure

## 1.1.4

* Upgrade docker-py to fix auth parsing issue

## 1.1.3

* Bump in release to fix pypi release process

## 1.1.2

* Bump in release to be able to publish to pypi

## 1.1.1

* Security release. [Ross Vandegrift](https://github.com/rvandegrift/) discovered a flaw in the proxy functionality when used in passthrough mode that would expose the host's IAM role credentials when extra paths were added to the end of the security-credentials end-point. metadataproxy will now properly capture any call to iam/security-credentials/<role> and return the scoped credentials, rather than the host's credentials.

## 1.1.0

* Added support for cross-account role assumption.

## 1.0

* Initial release
