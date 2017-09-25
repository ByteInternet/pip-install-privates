#!/usr/bin/env python
from setuptools import setup

setup(
    name='pip_install_privates',
    version='0.1',
    description='Install pip packages from private repositories without an ssh agent',
    author='Byte Internet',
    author_email='rickvandeloo@gmail.com',
    license='MIT',
    url='https://github.com/ByteInternet/pip_install_privates',
    packages=['pip_install_privates'],
    install_requires=['pip'],
    entry_points={
        'console_scripts': [
            'pip_install_privates = pip_install_privates.install:install'
        ]
    }
)
