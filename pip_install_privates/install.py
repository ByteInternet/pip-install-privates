#!/usr/bin/env python
import argparse
import os
try:
    from pip import status_codes, main as pip_main
except ImportError:
    from pip._internal import status_codes, main as pip_main


def convert_url(url, token):
    if url.startswith('git+ssh://git@github.com/'):
        return 'git+https://{}:x-oauth-basic@github.com/{}'.format(token, url[25:])
    elif url.startswith('git+git@github.com:'):
        return 'git+https://{}:x-oauth-basic@github.com/{}'.format(token, url[19:])
    return url

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
                collected.append(convert_url(tokens[0], transform_with_token))
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
                    collected.append(convert_url(tokens[1], transform_with_token))
                else:
                    collected.append('-e {}'.format(tokens[1]))
            else:
                # Strip development flag `-e` to prevent dependencies installed within the project
                collected += [tokens[1]]

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

    parser.add_argument('--token', '-t', help='Your Personal Access Token for private GitHub repositories')
    parser.add_argument('req_file', help='path to the requirements file to install')
    args = parser.parse_args()

    # TODO: rewrite to a clear collect and a clear transform phase. Or pass in a transform function
    pip_args = ['install'] + collect_requirements(args.req_file, transform_with_token=args.token)
    if pip_main(pip_args) != status_codes.SUCCESS:
        raise RuntimeError('Error installing requirements')


if __name__ == '__main__':
    install()
