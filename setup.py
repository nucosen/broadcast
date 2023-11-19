"""
Copyright 2022 NUCOSen運営会議

This file is part of NUCOSen Broadcast.

NUCOSen Broadcast is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

NUCOSen Broadcast is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with NUCOSen Broadcast.  If not, see <https://www.gnu.org/licenses/>.
"""

# NOTE : To build, use `py setup.py sdist`

from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

VERSION = {}

with open("./src/nucosen/__init__.py") as fp:
    exec(fp.read(), VERSION)

setup(
    name='nucosen',
    license="GNU AFFERO GENERAL PUBLIC LICENSE Version 3",
    version=VERSION.get("__version__", "0.0.0"),
    description='Broadcasting system for NUCOSen',
    url='https://github.com/nucosen/Broadcast',
    author='NUCOSen Management Committee',
    author_email='info@nucosen.live',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.10, <4',
    install_requires=open(
        "requirements.txt",
        encoding="utf-16"
    ).read().splitlines(),
    entry_points={
        'console_scripts': [
            'nucosen=nucosen.cli:execute',
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/nucosen/Broadcast/issues',
        'Funding': 'https://ofuse.me/nucosen',
        'Source': 'https://github.com/nucosen/Broadcast',
    },
)
