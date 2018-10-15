#!/usr/bin/env python
from setuptools import setup
from os.path import abspath, dirname, join


def readfile(filename):
    path = join(dirname(abspath(__file__)), filename)
    with open(path, 'rt') as filehandle:
        return filehandle.read()


setup(
    name='pip_install_privates',
    version='0.5',
    description='Install pip packages from private repositories without an ssh agent',
    long_description=readfile('README.rst'),
    author='Byte Internet',
    author_email='tech@byte.nl',
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
