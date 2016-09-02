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
from pip.req import parse_requirements

reqs_base = parse_requirements("requirements.txt", session=False)
reqs_wsgi = parse_requirements("requirements_wsgi.txt", session=False)
reqs = [str(ir.req) for ir in reqs_base]
reqs = reqs + [str(ir.req) for ir in reqs_wsgi]

setup(
    name="metadataproxy",
    version="1.1.4",
    packages=find_packages(exclude=["test*"]),
    install_requires=reqs,
    author="Ryan Lane",
    author_email="rlane@lyft.com",
    description=("A proxy for AWS's metadata service that gives out"
                 " scoped IAM credentials from STS"),
    license="apache2",
    url="https://github.com/lyft/metadataproxy"
)
