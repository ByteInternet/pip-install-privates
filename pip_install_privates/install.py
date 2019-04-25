#!/usr/bin/env python
import argparse
import os
from pip import __version__ as pip_version

from pip_install_privates.utils import parse_pip_version

pip_version_tuple = parse_pip_version(pip_version)
gte_18_1 = pip_version_tuple[0] == 18 and pip_version_tuple[1] >= 1
if pip_version_tuple[0] > 18 or gte_18_1:
    from pip._internal import main as pip_main
    from pip._internal.cli import status_codes

elif pip_version_tuple[0] >= 10:
    from pip._internal import status_codes, main as pip_main

else:
    from pip import status_codes, main as pip_main

GIT_SSH_PREFIX = 'git+ssh://git@github.com/'
GIT_GIT_PREFIX = 'git+git@github.com:'


def convert_to_github_url_with_token(url, token):
    """
    Convert a Github URL to a git+https url that identifies via an Oauth token. This allows for installation of
    private packages.
    :param url: The url to convert into a Github access token oauth url.
    :param token: The Github access token to use for the oauth url.
    :return: A git+https url with Oauth identification.
    """
    if url.startswith(GIT_SSH_PREFIX):
        return 'git+https://{}:x-oauth-basic@github.com/{}'.format(token, url[len(GIT_SSH_PREFIX):])
    elif url.startswith(GIT_GIT_PREFIX):
        return 'git+https://{}:x-oauth-basic@github.com/{}'.format(token, url[len(GIT_GIT_PREFIX):])
    return url


def convert_to_editable_github_url_with_token(url, token):
    """
    Convert a Github URL to an editable git+https url that identifies via an Oauth token. The Oauth identification
    allows for installation of private packages. The editable flag means the package
    will be installed as source (i.e. all files will be present instead of it just being installed as a package).
    :param url: The url to convert into a Github access token oauth url.
    :param token: The Github access token to use for the oauth url.
    :return: list: The editable flag for pip and a git+https url with Oauth identification.
    """
    url = convert_to_github_url_with_token(url, token)
    return ['-e', url]


def convert_to_editable_github_url(url):
    """
    Convert a Github URL to a git+https url (does not work for private packages). The editable flag means the package
    will be installed as source (i.e. all files will be present instead of it just being installed as a package).
    :param url: The url to convert into a Github access token oauth url.
    :return: list: The editable flag for pip and a git+https url.
    """
    if url.startswith(GIT_SSH_PREFIX):
        url = 'git+https://github.com/{}'.format(url[len(GIT_SSH_PREFIX):])
    elif url.startswith(GIT_GIT_PREFIX):
        url = 'git+https://github.com/{}'.format(url[len(GIT_GIT_PREFIX):])
    return ['-e', url]


def collect_requirements(fname, transform_with_token=None):
    with open(fname) as reqs:
        contents = reqs.readlines()

    collected = []
    for line in contents:
        line = line.strip()

        if not line or line.startswith('#'):
            continue

        tokens = line.split()

        # Handles:
        #   alembic>=0.8
        #   alembic==0.8.8
        #   alembic==0.8.8  # so we can apply Hypernode/ByteDB fixtures
        #   git+git://github.com/myself/myproject
        #   git+ssh://github.com/myself/myproject@v2
        #
        if len(tokens) == 1 or tokens[1].startswith('#'):
            if (tokens[0].startswith('git+ssh') or tokens[0].startswith('git+git')) and transform_with_token:
                collected.append(convert_to_github_url_with_token(tokens[0], transform_with_token))
            else:
                collected.append(tokens[0])


        # Handles:
        #   -r base.txt
        elif tokens[0] == '-r':
            curdir = os.path.abspath(os.path.dirname(fname))
            collected += collect_requirements(os.path.join(curdir, tokens[1]),
                                              transform_with_token=transform_with_token)

        # Rewrite private repositories that normally would use ssh (with keys in an agent), to using
        # an oauth key
        elif tokens[0] == '-e':
            if tokens[1].startswith('git+ssh') or tokens[1].startswith('git+git'):
                if transform_with_token:
                    collected += convert_to_editable_github_url_with_token(tokens[1], transform_with_token)
                else:
                    collected += convert_to_editable_github_url(tokens[1])
            else:
                collected += ['-e', tokens[1]]

        # No special casing for the rest. Just pass everything to pip
        else:
            collected += tokens

    return collected


def install():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
Install all requirements from specified file with pip. Optionally transform
git+git and git+ssh url to private repo's to use a given Personal Access Token for
github. That way installing them does not depend on a ssh-agent with suitable
keys. Which you don't have when installing requirements in a Docker.
These URLs will also be stripped of the -e flag, so they're installed globally.
Note the -e flag is optional for the git+git//github.com and git+ssh://github.com
urls.

This means that the following URL:
  -e git+git@github.com:MyOrg/my-project.git@my-tag#egg=my_project
would be transformed to:
  git+https://<token>:x-oauth-basic@github.com/MyOrg/my-project.git@my-tag#egg=my_project

Non-private GitHub URL's (git+https) and non-GitHub URL's are kept as-is, but
are also stripped of the -e flag. If no token is given, private URLs will be
kept, including the -e flag (otherwise they can't be installed at all).
""")

    parser.add_argument('--token', '-t', help='Your Personal Access Token for private GitHub repositories',
                        default=os.environ.get('GITHUB_TOKEN'))
    parser.add_argument('req_file', help='path to the requirements file to install')
    args = parser.parse_args()

    # TODO: rewrite to a clear collect and a clear transform phase. Or pass in a transform function
    pip_args = ['install'] + collect_requirements(args.req_file, transform_with_token=args.token)
    if pip_main(pip_args) != status_codes.SUCCESS:
        raise RuntimeError('Error installing requirements')


if __name__ == '__main__':
    install()
