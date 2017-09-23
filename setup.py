#!/usr/bin/env python
from setuptools import setup

setup(
    name='pipprivates',
    version='0.1',
    description='Install pip packages from private repositories without an ssh agent',
    author='Byte Internet',
    author_email='rickvandeloo@gmail.com',
    license='MIT',
    url='https://github.com/ByteInternet/pip-install-privates',
    packages=['pipprivates'],
    install_requires=['pip'],
    entry_points={
        'console_scripts': [
            'pip-install-privates = pipprivates.install:install'
        ]
    }
)
