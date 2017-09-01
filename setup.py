#
# Copyright (c) 2016, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
""" This module provides a RESTful API client for Cloudvision(R) Portal (CVP)
    which can be used for building applications that work with Arista CVP.
"""
import io
from os import path, walk
from glob import glob

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from cvprac import __version__, __author__

def find_modules(pkg):
    ''' Return all modules from the pkg
    '''
    modules = [pkg]
    for dirname, dirnames, _ in walk(pkg):
        for subdirname in dirnames:
            modules.append(path.join(dirname, subdirname))
    return modules

def get_long_description():
    ''' Get the long description from README.rst if it exists.
        Null string is returned if README.rst is non-existent
    '''
    long_description = ''
    here = path.abspath(path.dirname(__file__))
    try:
        with io.open(path.join(here, 'README.rst'), encoding='utf-8') as file_hdl:
            long_description = file_hdl.read()
    except IOError:
        pass
    return long_description

setup(
    name='cvprac',
    version=__version__,
    description='Arista Cloudvision(R) Portal Rest API Client written in python',
    long_description=get_long_description(),
    author=__author__,
    author_email='eosplus-dev@arista.com',
    url='https://github.com/aristanetworks/cvprac',
    download_url='https://github.com/aristanetworks/cvprac/tarball/%s' % __version__,
    license='BSD-3',
    packages=find_modules('cvprac'),

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',

        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: BSD License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    # What does your project relate to?
    keywords='networking CloudVision development rest api',

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['requests>=1.0.0'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev]
    extras_require={
        'dev': ['check-manifest', 'pep8', 'pyflakes', 'pylint', 'coverage',
                'pyyaml'],
    },
)
