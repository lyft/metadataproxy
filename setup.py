# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    reqs_base = f.read().splitlines()
    reqs_base = [r for r in reqs_base if not r.startswith('#') and r]

with open('requirements_wsgi.txt') as f:
    reqs_wsgi = f.read().splitlines()
    reqs_wsgi = [r for r in reqs_wsgi if not r.startswith('#') and r]

reqs = reqs_base + reqs_wsgi

setup(
    name="metadataproxy",
    version="1.5.2",
    packages=find_packages(exclude=["test*"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=reqs,
    author="Ryan Lane",
    author_email="rlane@lyft.com",
    description=("A proxy for AWS's metadata service that gives out"
                 " scoped IAM credentials from STS"),
    license="apache2",
    url="https://github.com/lyft/metadataproxy"
)
