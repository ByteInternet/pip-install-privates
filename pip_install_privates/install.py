#!/usr/bin/env python
import argparse
import os
from pip import __version__ as pip_version
from pip_install_privates.utils import parse_pip_version

# Determine the pip version and set appropriate imports
pip_version_tuple = parse_pip_version(pip_version)
gte_18_1 = pip_version_tuple[0] == 18 and pip_version_tuple[1] >= 1

if pip_version_tuple[0] >= 19 and pip_version_tuple[1] >= 3:
    from pip._internal.main import main as pip_main
    from pip._internal.cli import status_codes
elif pip_version_tuple[0] > 18 or gte_18_1:
    from pip._internal import main as pip_main
    from pip._internal.cli import status_codes
elif pip_version_tuple[0] >= 10:
    from pip._internal import status_codes, main as pip_main
else:
    from pip import status_codes, main as pip_main

# Define URL prefixes
GIT_SSH_PREFIX = "git+ssh://git@github.com/"
GIT_GIT_PREFIX = "git+git@github.com:"
GIT_HTTPS_PREFIX = "git+https://github.com/"

GITLAB_DEFAULT_DOMAIN = "gitlab.com"
GIT_SSH_PREFIX_GITLAB = "git+ssh://git@"
GIT_GIT_PREFIX_GITLAB = "git+git@"
GIT_HTTPS_PREFIX_GITLAB = "git+https://"


def convert_to_github_url_with_token(url, token):
    """
    Convert a GitHub URL to a git+https URL that uses an OAuth token.
    This allows for the installation of private packages.
    :param url: The URL to convert into a GitHub access token OAuth URL.
    :param token: The GitHub access token to use for the OAuth URL.
    :return: A git+https URL with OAuth identification.
    """
    for prefix in [GIT_SSH_PREFIX, GIT_GIT_PREFIX, GIT_HTTPS_PREFIX]:
        if url.startswith(prefix):
            return f"git+https://{token}:x-oauth-basic@github.com/{url[len(prefix):]}"
    return url


def convert_to_gitlab_url_with_token(url, token, gitlab_domain=None):
    """
    Convert a GitLab URL to a git+https URL that uses an OAuth token.
    This allows for the installation of private packages.
    :param url: The URL to convert into a GitLab access token OAuth URL.
    :param token: The GitLab access token to use for the OAuth URL.
    :param gitlab_domain: The domain of the GitLab instance.
    :return: A git+https URL with OAuth identification.
    """
    domain = gitlab_domain if gitlab_domain else GITLAB_DEFAULT_DOMAIN
    prefixes = [
        GIT_SSH_PREFIX_GITLAB + domain + "/",
        GIT_GIT_PREFIX_GITLAB + domain + ":",
        GIT_HTTPS_PREFIX_GITLAB + domain + "/",
    ]
    for prefix in prefixes:
        if url.startswith(prefix):
            return f"git+https://gitlab-ci-token:{token}@{domain}/{url[len(prefix):]}"
    return url


def convert_to_github_url(url):
    """
    Convert a GitHub URL to a git+https URL without using an OAuth token.
    :param url: The URL to convert.
    :return: A git+https URL.
    """
    for prefix in [GIT_SSH_PREFIX, GIT_GIT_PREFIX]:
        if url.startswith(prefix):
            return f"git+https://github.com/{url[len(prefix):]}"
    return url


def convert_to_gitlab_url(url, gitlab_domain=None):
    """
    Convert a GitLab URL to a git+https URL without using an OAuth token.
    :param url: The URL to convert.
    :param gitlab_domain: The domain of the GitLab instance.
    :return: A git+https URL.
    """
    domain = gitlab_domain if gitlab_domain else GITLAB_DEFAULT_DOMAIN
    prefixes = [
        GIT_SSH_PREFIX_GITLAB + domain + "/",
        GIT_GIT_PREFIX_GITLAB + domain + ":",
        GIT_HTTPS_PREFIX_GITLAB + domain + "/",
    ]
    for prefix in prefixes:
        if url.startswith(prefix):
            return f"git+https://{domain}/{url[len(prefix):]}"
    return url


def can_convert_url(url):
    """
    Determine if the URL can be converted.
    :param url: The URL to check.
    :return: True if the URL can be converted, False otherwise.
    """
    return (
        url.startswith("git+ssh")
        or url.startswith("git+git")
        or url.startswith("git+https")
    )


def add_potential_pip_environment_markers_to_requirement(stripped_tokens, requirement):
    """
    Append pip environment markers to the requirement if present.
    :param stripped_tokens: The tokens from the requirement line.
    :param requirement: The base requirement.
    :return: The requirement with pip environment markers appended.
    """
    try:
        pip_environment_marker_index = stripped_tokens.index(";")
    except ValueError:
        return requirement
    environment_index = pip_environment_marker_index + 1
    return f"{requirement} ; {stripped_tokens[environment_index]}"


def convert_potential_git_url(
    requirement,
    tokens,
    transform_with_token=False,
    gitlab_domain=None,
    ci_job_token=None,
):
    """
    Convert a potential Git URL to a git+https URL, optionally using an OAuth token.
    :param requirement: The potential URL to convert.
    :param tokens: All specifications provided for the requirement.
    :param transform_with_token: The OAuth token to use for GitHub URLs.
    :param gitlab_domain: The domain of the GitLab instance for GitLab URLs.
    :param ci_job_token: The CI job token for GitLab URLs.
    :return: A list containing the converted URL.
    """
    if can_convert_url(requirement):
        if "gitlab.com" in requirement or (
            gitlab_domain and f"@{gitlab_domain}" in requirement
        ):
            domain = gitlab_domain if gitlab_domain else GITLAB_DEFAULT_DOMAIN
            if ci_job_token:
                git_url = convert_to_gitlab_url_with_token(
                    requirement, ci_job_token, domain
                )
            else:
                git_url = convert_to_gitlab_url(requirement, domain)
        elif transform_with_token:
            git_url = convert_to_github_url_with_token(
                requirement, transform_with_token
            )
        else:
            git_url = convert_to_github_url(requirement)
        git_url = add_potential_pip_environment_markers_to_requirement(tokens, git_url)
        return [git_url]
    return [add_potential_pip_environment_markers_to_requirement(tokens, requirement)]


def convert_potential_editable_git_url(
    requirement,
    tokens,
    transform_with_token=False,
    gitlab_domain=None,
    ci_job_token=None,
):
    """
    Convert a potential editable Git URL to a git+https URL, optionally using an OAuth token.
    :param requirement: The potential URL to convert.
    :param tokens: All specifications provided for the requirement.
    :param transform_with_token: The OAuth token to use for GitHub URLs.
    :param gitlab_domain: The domain of the GitLab instance for GitLab URLs.
    :param ci_job_token: The CI job token for GitLab URLs.
    :return: A list containing the editable flag and the converted URL.
    """
    requirement_tokens = convert_potential_git_url(
        requirement, tokens, transform_with_token, gitlab_domain, ci_job_token
    )
    requirement_tokens.insert(0, "-e")
    return requirement_tokens


def collect_requirements(
    fname,
    transform_with_token=None,
    gitlab_domain=None,
    ci_job_token=None,
    github_root_dir=None,
):
    """
    Collect and transform requirements from a file.
    :param fname: The path to the requirements file.
    :param transform_with_token: The OAuth token to use for GitHub URLs.
    :param gitlab_domain: The domain of the GitLab instance for GitLab URLs.
    :param ci_job_token: The CI job token for GitLab URLs.
    :param github_root_dir: Specifies the base directory on GitHub to be transformed when applying the private tag.
    :return: A list of collected and transformed requirements.
    """
    with open(fname) as reqs:
        contents = reqs.readlines()

    collected = []
    for line in contents:
        line = line.strip()

        if "github.com/" in line and "#pip-private" in line:
            line = transform_github_to_gitlab(
                line, ci_job_token, gitlab_domain, github_root_dir
            )

        # Replace environment variable placeholders
        if gitlab_domain:
            line = line.replace("${GITLAB_DOMAIN}", gitlab_domain)

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        tokens = line.split()

        # Handles:
        #   alembic>=0.8
        #   alembic==0.8.8
        #   alembic==0.8.8  # so we can apply Hypernode/ByteDB fixtures
        #   git+git://github.com/myself/myproject
        #   git+ssh://github.com/myself/myproject@v2

        if len(tokens) == 1 or tokens[1].startswith("#"):
            if can_convert_url(tokens[0]):
                if gitlab_domain and f"{gitlab_domain}" in tokens[0]:
                    if ci_job_token:
                        collected.append(
                            convert_to_gitlab_url_with_token(
                                tokens[0], ci_job_token, gitlab_domain
                            )
                        )
                    else:
                        collected.append(
                            convert_to_gitlab_url(tokens[0], gitlab_domain)
                        )
                elif "github.com/" in line and "#pip-private" in line:
                    line = transform_github_to_gitlab(
                    line, ci_job_token, gitlab_domain, github_root_dir
            )
                
                elif transform_with_token:
                    collected.append(
                        convert_to_github_url_with_token(
                            tokens[0], transform_with_token
                        )
                    )
                else:
                    collected.append(tokens[0])
            else:
                collected.append(tokens[0])

        # Handles:
        #   -r base.txt
        elif tokens[0] == "-r":
            curdir = os.path.abspath(os.path.dirname(fname))
            collected += collect_requirements(
                os.path.join(curdir, tokens[1]),
                transform_with_token=transform_with_token,
                gitlab_domain=gitlab_domain,
                ci_job_token=ci_job_token,
            )

        # Rewrite private repositories that normally would use ssh (with keys in an agent), to using
        # an oauth key
        elif tokens[0] == "-e":
            # Remove any single quotes that might be present. This is for cases where an editable is used with pip
            # environment markers. It has to be quoted in those cases, i.e.:
            # -e 'git+git@github.com:ByteInternet/my-repo.git@20201127.1#egg=my-repo ; python_version=="3.7"'
            # Do not remove double quotes, since these could be used in the environment marker string i.e. "3.7".
            stripped_tokens = [token.replace("'", "") for token in tokens]
            if gitlab_domain and f"{gitlab_domain}" in stripped_tokens[1]:
                collected += convert_potential_editable_git_url(
                    stripped_tokens[1],
                    stripped_tokens,
                    ci_job_token=ci_job_token,
                    gitlab_domain=gitlab_domain,
                )
            elif "gitlab.com" in stripped_tokens[1] and ci_job_token:
                collected += convert_potential_editable_git_url(
                    stripped_tokens[1],
                    stripped_tokens,
                    ci_job_token=ci_job_token,
                )
            else:
                collected += convert_potential_editable_git_url(
                    stripped_tokens[1],
                    stripped_tokens,
                    transform_with_token=transform_with_token,
                )

        # Handles:
        #   git+git://github.com/myself/myproject ; python_version=="2.7"
        #   git+ssh://github.com/myself/myproject@v2 ; python_version=="3.6"
        #
        elif ";" in tokens:
            collected += convert_potential_git_url(
                tokens[0],
                tokens,
                transform_with_token=transform_with_token,
                gitlab_domain=gitlab_domain,
                ci_job_token=ci_job_token,
            )

        # No special casing for the rest. Just pass everything to pip
        else:
            collected += tokens

    return collected


def transform_github_to_gitlab(line, ci_job_token, gitlab_domain, github_root_dir):
    # Define possible URL prefixes for GitHub URLs
    prefixes = [GIT_SSH_PREFIX, GIT_GIT_PREFIX, GIT_HTTPS_PREFIX]

    # Check each prefix to see if it appears in the line with the transform directory and the private marker
    for prefix in prefixes:
        search_pattern = f"{prefix}{github_root_dir}/"  # Ensure the slash is there to correctly identify the directory
        if search_pattern in line and "#pip-private" in line:
            parts = line.split("#pip-private")[0].strip()
            repo_part = parts.split(search_pattern)[1]
            new_url = f"git+https://gitlab-ci-token:{ci_job_token}@{gitlab_domain}/{repo_part}"
            return new_url

    return line


def install():
    """
    Install all requirements from the specified file with pip, optionally transforming URLs to use OAuth tokens.
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
    Installs packages from a specified requirements file using pip, with the ability to transform repository URLs for private access using personal access tokens. This script is particularly useful in environments that lack SSH agent support, such as Docker containers, ensuring seamless installations of packages from private repositories.

    Features:
    - Transforms git+git and git+ssh URLs for GitHub and GitLab to use HTTPS with personal access tokens. This facilitates installations without an SSH agent.
    - Automatically strips the -e (editable) flag from URLs to enforce global installation, enhancing consistency and stability in production environments.
    - Supports custom GitLab instances by replacing GitHub URLs with GitLab URLs using environment-specific variables, which is useful for maintaining public GitHub URLs in your requirements file but needing to fetch from GitLab during installation.

    URL Transformation Examples:
    - GitHub:
      From: -e git+git@github.com:MyOrg/my-project.git@my-tag#egg=my_project
      To: git+https://<token>:x-oauth-basic@github.com/MyOrg/my-project.git@my-tag#egg=my_project
    
    - GitLab:
      From: -e git+git@gitlab.com:MyOrg/my-project.git@my-tag#egg=my_project
      To: git+https://gitlab-ci-token:<token>@gitlab.com/MyOrg/my-project.git@my-tag#egg=my_project
    
    - Custom GitLab Instance:
      To transform URLs with a private tag and map them to a GitLab domain, ensure the following environment variables are set:
        CI_TOKEN = <token>, GITLAB_DOMAIN = <your-gitlab-domain>, GITHUB_ROOT_DIR = <github-root-directory>
      Example where GITHUB_ROOT_DIR = ByteInternet:
        From: git+ssh://git@github.com/ByteInternet/my-project.git@my-tag#egg=my_project #pip-private
        To: git+https://gitlab-ci-token:<token>@<your-gitlab-domain>/my-project.git@my-tag#egg=my_project

    Note:
    - Non-private GitHub and GitLab URLs (git+https) and non-GitHub/GitLab URLs remain unchanged, except for the removal of the -e flag.
    - If no token is provided, private URLs retain the -e flag, preserving their editable state to ensure they can still be installed when manual authentication is configured.

    Arguments:
    - --token/-t: Personal Access Token for private GitHub repositories.
    - --gitlab-token: Personal Access Token for private GitLab repositories.
    - --github-root-dir: Base directory on GitHub for URL transformations to GitLab domains, assisting in URL mappings.
    - req_file: Path to the requirements file to be processed and installed.
    """,
    )

    parser.add_argument(
        "--token",
        "-t",
        help="Your Personal Access Token for private GITHUB repositories",
        default=os.environ.get("GITHUB_TOKEN"),
    )
    parser.add_argument(
        "--gitlab-token",
        help="Enable your Personal Access Token for GitLab private repositories",
        default=os.environ.get("CI_JOB_TOKEN"),
    )

    parser.add_argument(
        "--github-root-dir",
        help=(
            "Specifies the base directory on GitHub to be transformed when applying the private tag. "
            "For example, if '--github-root-dir=ByteInternet' is set, any URL starting with 'github.com/ByteInternet' "
            "will be transformed to use the configured GitLab domain. This directory acts as a root folder in URL transformations."
        ),
        default=os.environ.get("GITHUB_ROOT_DIR"),
    )
    parser.add_argument("req_file", help="path to the requirements file to install")
    args = parser.parse_args()

    gitlab_domain = os.environ.get("GITLAB_DOMAIN")
    pip_args = ["install"] + collect_requirements(
        args.req_file,
        transform_with_token=args.token,
        gitlab_domain=gitlab_domain,
        ci_job_token=args.gitlab_token,
    )
    if pip_main(pip_args) != status_codes.SUCCESS:
        raise RuntimeError("Error installing requirements")


if __name__ == "__main__":
    install()
