#!/usr/bin/env python
import argparse
import os
import pip
from pip.status_codes import SUCCESS


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
        if len(tokens) == 1 or tokens[1].startswith('#'):
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
            if tokens[1].startswith('git+git@github.com:'):
                vcs_url = 'git+https://{}:x-oauth-basic@github.com/{}'.format(
                    transform_with_token, tokens[1][19:]) if transform_with_token else tokens[1]

                collected += [vcs_url]
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
Install all requirements from specified file with pip. Optionally transforms URL's
to our private repo's to use a given Personal Access Token for github. That way
installing them does not depend on a ssh-agent with suitable keys. Which you don't
have when installing requirements in a Docker.

This means that the following URL:
    -e git+git@github.com:ByteInternet/our-private-project.git@our-tag#egg=our_private_project
would be transformed to:
    -e git+https://<token>:x-oauth-basic@github.com/ByteInternet/our-private-project.git@our-tag#egg=our_private_project

Non-private GitHub URL's and non-GitHub URL's are treated as-is.'
""")

    parser.add_argument('req_file', help='path to the requirements file to install')
    parser.add_argument('--token', '-t', help='Your Personal Access Token for private GitHub repositories')
    args = parser.parse_args()

    # TODO: rewrite to a clear collect and a clear transform phase. Or pass in a transform function
    pip_args = ['install'] + collect_requirements(args.req_file, transform_with_token=args.token)
    if pip.main(pip_args) != SUCCESS:
        raise RuntimeError('Error installing requirements')


if __name__ == '__main__':
    install()
