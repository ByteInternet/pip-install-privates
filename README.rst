pip_install_privates
====================

.. image:: https://codecov.io/github/ByteInternet/pip-install-privates/coverage.svg?branch=master
    :target: https://codecov.io/github/ByteInternet/pip-install-privates
    :alt: codecov.io

.. image:: https://travis-ci.org/ByteInternet/pip-install-privates.svg?branch=master
    :target: https://travis-ci.org/ByteInternet/pip-install-privates
    :alt: travis-ci.org

Install pip packages from private Github repositories without an SSH agent.

Installation
------------

Get it from `pypi <https://pypi.python.org/pypi/pip-install-privates/>`_:

.. code-block:: bash

    pip install pip_install_privates

Or install directly from GitHub:

.. code-block:: bash

    pip install git+https://github.com/ByteInternet/pip-install-privates.git@master#egg=pip-install-privates

Usage
-----

To use pip_install_privates, you need a Personal Access Token from Github. Go to `Settings → Personal access tokens <https://github.com/settings/tokens>`_ and click "Generate new token". Make sure to give the "repo" permission ("Full control of private repositories"). Copy the generated token and store it somewhere safe. Then use it in the command below:

.. code-block:: bash

    pip_install_privates --token $GITHUB_TOKEN requirements.txt

Run ``pip_install_privates --help`` for more information.

Developing
----------

After ``git clone``ing the repository, create a virtualenv however you prefer, for example:

.. code-block:: bash

    mkvirtualenv -a $PWD pip_install_privates

Install the package, its dependencies and dev dependencies:

.. code-block:: bash

    pip install -e . -r requirements.txt

Run tests for your specific Python verison:

.. code-block:: bash

    nosetests

Or for all Python versions:

.. code-block:: bash

    tox

About
=====

This software is brought to you by Byte, a webhosting provider based in Amsterdam, The Netherlands. We specialize in fast and secure Magento hosting and scalable cluster hosting.

Check out our `Github page <https://github.com/ByteInternet>`_ for more open source software or `our site <https://www.byte.nl>`_ to learn about our products and technologies. Look interesting? Reach out about joining `the team <https://www.byte.nl/vacatures>`_. Or just drop by for a cup of excellent coffee if you're in town!
