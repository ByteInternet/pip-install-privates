pip_install_privates
====================

.. image:: https://codecov.io/github/ByteInternet/pip-install-privates/coverage.svg?branch=master
    :target: https://codecov.io/github/ByteInternet/pip-install-privates
    :alt: codecov.io

.. image:: https://travis-ci.org/ByteInternet/pip-install-privates.svg?branch=master
    :target: https://travis-ci.org/ByteInternet/pip-install-privates
    :alt: travis-ci.org

Install pip packages from private GitHub repositories without an SSH agent.

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

Run ``pip_install_privates --help`` for more information.

To use `pip_install_privates`, you need a Personal Access Token from GitHub or GitLab.

GitHub
------

1. Generate a Personal Access Token from GitHub with the required scopes. Go to `Settings → Personal access tokens <https://github.com/settings/tokens>`_ and click "Generate new token". Make sure to give the "repo" permission ("Full control of private repositories"). Copy the generated token and store it somewhere safe.
2. Store the token as an environment variable:

.. code-block:: bash

    export GITHUB_TOKEN=your_github_token

GitLab
------

1. On the left sidebar, select "Search or go to" and find your project.
2. Select Settings > CI/CD.
3. Expand "Token Access".
4. Ensure the "Limit access to this project" toggle is enabled. This is enabled by default in new projects. It is a security risk to disable this feature, so project maintainers or owners should keep this setting enabled at all times.
5. Select "Add group or project".
6. Input the path to the group or project to add to the allowlist, and select "Add project".
7. This will be used with `CI_JOB_TOKEN`.

GitLab Domain
-------------

When using a custom domain:
1. Generate a Personal Access Token from GitLab with the required scopes.
2. Store the token as an environment variable:
3. Specify your GitLab domain (if using a custom GitLab instance):

.. code-block:: bash

    export GITLAB_DOMAIN=your.gitlab.domain

Running the Script
------------------

If using a custom GitLab domain, ensure your `requirements.txt` or `base.txt` contains the domain variable you wish to mask. Example below:

.. code-block:: bash

    git+https://${GITLAB_DOMAIN}/your-repo.git@20240227.1#egg=your-repo
    git+https://github.com/your_org/your_repo.git@v1.0.0#egg=your_package

Run the script with the token:

.. code-block:: bash

    pip_install_privates --token $GITHUB_TOKEN --gitlab-token $CI_JOB_TOKEN requirements.txt

Run `pip_install_privates --help` for more information.

Without Token
-------------

If no token is provided, the script will use the default URLs. Ensure you have the necessary permissions set up for public repositories.

Developing
----------

After performing ``git clone`` on the repository, create a virtual environment however you prefer. For example:

.. code-block:: bash

    mkvirtualenv -a $PWD pip_install_privates

Install the package, its dependencies, and dev dependencies:

.. code-block:: bash

    pip install -e . -r requirements.txt

Run tests for your specific Python version:

.. code-block:: bash

    nosetests

Or for all Python versions:

.. code-block:: bash

    tox

About
=====

This software is brought to you by Hypernode, a web hosting provider based in Amsterdam, The Netherlands. We specialize in fast and secure Magento hosting and scalable cluster hosting.

Check out our `GitHub page <https://github.com/ByteInternet>`_ for more open source software or `our site <https://www.hypernode.com>`_ to learn about our products and technologies. Look interesting? Reach out about joining `the team <https://www.hypernode.com/vacatures>`_. Or just drop by for a cup of excellent coffee if you're in town!
