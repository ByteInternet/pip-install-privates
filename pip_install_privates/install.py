#!/usr/bin/env python
import argparse, logging
import os
from pip import __version__ as pip_version
from pip_install_privates.utils import parse_pip_version

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
            transformed_url = (
                f"git+https://{token}:x-oauth-basic@github.com/{url[len(prefix):]}"
            )
            logger.debug(f"Transformed GitHub URL with token: {transformed_url}")
            return transformed_url
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
            transformed_url = (
                f"git+https://gitlab-ci-token:{token}@{domain}/{url[len(prefix):]}"
            )
            logger.debug(f"Transformed GitLab URL with token: {transformed_url}")
            return transformed_url
    return url


def convert_to_github_url(url):
    """
    Convert a GitHub URL to a git+https URL without using an OAuth token.
    :param url: The URL to convert.
    :return: A git+https URL.
    """
    for prefix in [GIT_SSH_PREFIX, GIT_GIT_PREFIX]:
        if url.startswith(prefix):
            transformed_url = f"git+https://github.com/{url[len(prefix):]}"
            logger.debug(f"Transformed GitHub URL: {transformed_url}")
            return transformed_url
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
            transformed_url = f"git+https://{domain}/{url[len(prefix):]}"
            logger.debug(f"Transformed GitLab URL: {transformed_url}")
            return transformed_url
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
        logger.debug(f"Converted potential Git URL: {git_url}")
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
    logger.debug(f"Converted potential editable Git URL: {requirement_tokens}")
    return requirement_tokens


def collect_requirements(
    fname,
    transform_with_token=None,
    gitlab_domain=None,
    ci_job_token=None,
    github_root_dir=None,
    project_names=None,
):
    """
    Collect and transform requirements from a file.
    :param fname: The path to the requirements file.
    :param transform_with_token: The OAuth token to use for GitHub URLs.
    :param gitlab_domain: The domain of the GitLab instance for GitLab URLs.
    :param ci_job_token: The CI job token for GitLab URLs.
    :param github_root_dir: Specifies the base directory on GitHub to be transformed when applying the private tag.
    :param project_names: Comma-separated string of project names to look for in the GitHub URLs.
    :param no_auth: Convert URLs to HTTPS without authentication.
    :return: A list of collected and transformed requirements.
    """
    if project_names is None:
        project_names = os.environ.get("PROJECT_NAMES", "")
    project_names = [proj.strip() for proj in project_names.split(",")]

    logger.debug(f"Collecting requirements from {fname}")
    logger.debug(f"Using GitHub root dir: {github_root_dir}")
    logger.debug(f"Using project names: {project_names}")

    with open(fname) as reqs:
        contents = reqs.readlines()

    collected = []
    for line in contents:
        original_line = line.strip()
        logger.debug(f"Processing line: {original_line}")

        # Early transform check before any other processing
        if "github.com/" in original_line:
            for proj in project_names:
                if proj in original_line:
                    logger.debug(f"Line before GitHub to GitLab transform: {original_line}")
                    logger.debug(f"proj is: {proj}")
                    line = transform_github_to_gitlab(
                        original_line,
                        ci_job_token,
                        gitlab_domain,
                        github_root_dir,
                        project_names,
                    )
                else: 
                    line = convert_to_github_url(original_line)
                logger.debug(f"Line after transformation: {line}")
                break  # Exit the loop once a transformation has been done
        else:
            line = original_line

        # Replace environment variable placeholders
        if gitlab_domain:
            line = line.replace("${GITLAB_DOMAIN}", gitlab_domain)

        # Skip empty lines and comments
        if not line or line.startswith("#"):
            continue

        tokens = line.split()

        # Handles:
        #   -r base.txt
        if tokens[0] == "-r":
            curdir = os.path.abspath(os.path.dirname(fname))
            logger.debug(f"Recursively collecting requirements from: {tokens[1]}")
            collected += collect_requirements(
                os.path.join(curdir, tokens[1]),
                transform_with_token=transform_with_token,
                gitlab_domain=gitlab_domain,
                ci_job_token=ci_job_token,
                github_root_dir=github_root_dir,
                project_names=",".join(project_names),  # Ensure project names are passed correctly
            )
            continue

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
                elif transform_with_token:
                    collected.append(
                        convert_to_github_url_with_token(
                            tokens[0], transform_with_token
                        )
                    )
                elif not transform_with_token:
                    collected.append(convert_to_github_url(tokens[0]))
                else:
                    collected.append(tokens[0])
            else:
                collected.append(tokens[0])

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


def transform_github_to_gitlab(
    line, ci_job_token, gitlab_domain, github_root_dir, project_names
):
    prefixes = [GIT_SSH_PREFIX, GIT_GIT_PREFIX, GIT_HTTPS_PREFIX]

    for prefix in prefixes:
        for project_name in project_names:
            search_pattern = f"{prefix}{github_root_dir}/{project_name}"
            if search_pattern in line:
                parts = line.split("#")[0].strip()
                try:
                    repo_part = parts.split(f"{prefix}{github_root_dir}/")[1]
                except IndexError:
                    logger.error(f"Error processing line: {line}")
                    continue

                new_url = f"git+https://gitlab-ci-token:{ci_job_token}@{gitlab_domain}/{repo_part}"

                if "#egg=" in line:
                    egg_part = line.split("#egg=")[1].split()[0]
                    new_url = f"{new_url}#egg={egg_part}"

                logger.debug(f"Transformed GitHub to GitLab URL: {new_url}")
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
      To transform URLs and map them to a GitLab domain, ensure the following environment variables are set:
        CI_TOKEN = <token>, GITLAB_DOMAIN = <your-gitlab-domain>, GITHUB_ROOT_DIR = <github-root-directory>, PROJECT_NAMES = <comma-separated-project-names>
      Example where GITHUB_ROOT_DIR = ByteInternet:
        From: git+ssh://git@github.com/ByteInternet/my-project.git@my-tag#egg=my_project
        To: git+https://gitlab-ci-token:<token>@<your-gitlab-domain>/my-project.git@my-tag#egg=my_project

    Note:
    - Non-private GitHub and GitLab URLs (git+https) and non-GitHub/GitLab URLs remain unchanged, except for the removal of the -e flag.
    - If no token is provided, private URLs retain the -e flag, preserving their editable state to ensure they can still be installed when manual authentication is configured.

    Arguments:
    - --token/-t: Personal Access Token for private GitHub repositories.
    - --gitlab-token: Personal Access Token for private GitLab repositories.
    - --github-root-dir: Base directory on GitHub for URL transformations to GitLab domains, assisting in URL mappings.
    - --gitlab-domain: Domain of the GitLab instance for URL transformations.
    - --project-names: Comma-separated list of project names to look for in the GitHub URLs.
    - req_file: Path to the requirements file to install.
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

    parser.add_argument(
        "--gitlab-domain",
        help="Domain of the GitLab instance for URL transformations.",
        default=os.environ.get("GITLAB_DOMAIN"),
    )

    parser.add_argument(
        "--project-names",
        help="Comma-separated list of project names to look for in the GitHub URLs.",
        default=os.environ.get("PROJECT_NAMES"),
    )

    parser.add_argument("req_file", help="path to the requirements file to install")
    args = parser.parse_args()

    gitlab_domain = args.gitlab_domain or os.environ.get("GITLAB_DOMAIN")
    ci_job_token = args.gitlab_token or os.environ.get("CI_JOB_TOKEN")
    github_root_dir = args.github_root_dir or os.environ.get("GITHUB_ROOT_DIR")
    project_names = args.project_names or os.environ.get("PROJECT_NAMES")

    logger.debug(
        f"Arguments received: token={args.token}, gitlab_token={ci_job_token}, gitlab_domain={gitlab_domain}, github_root_dir={github_root_dir}, project_names={project_names}"
    )

    pip_args = ["install"] + collect_requirements(
        args.req_file,
        transform_with_token=args.token,
        gitlab_domain=gitlab_domain,
        ci_job_token=ci_job_token,
        github_root_dir=github_root_dir,
        project_names=project_names,
    )
    if pip_main(pip_args) != status_codes.SUCCESS:
        raise RuntimeError("Error installing requirements")


if __name__ == "__main__":
    install()
