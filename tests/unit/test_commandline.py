try:
    # python 2
    from StringIO import StringIO
except ImportError:
    # python 3
    from io import StringIO

from unittest import TestCase

import sys
from mock import patch

from pip_install_privates.install import install, status_codes


class TestCommandLine(TestCase):

    def setUp(self):
        collect_patcher = patch("pip_install_privates.install.collect_requirements")
        self.addCleanup(collect_patcher.stop)
        self.mock_collect = collect_patcher.start()

        pip_patcher = patch("pip_install_privates.install.pip_main")
        self.addCleanup(pip_patcher.stop)
        self.mock_pip = pip_patcher.start()
        self.mock_pip.return_value = status_codes.SUCCESS

    def test_commandline_passes_requirements_file_to_collect(self):
        with patch.object(sys, "argv", ["pip-install", "requirements.txt"]):
            install()

        self.mock_collect.assert_called_once_with(
            "requirements.txt",
            transform_with_token=None,
            gitlab_domain=None,
            ci_job_token=None,
            github_root_dir=None,
            project_names=None,
        )

    def test_commandline_passes_specified_token_to_collect(self):
        with patch.object(
            sys, "argv", ["pip-install", "-t", "my-token", "requirements.txt"]
        ):
            install()

        self.mock_collect.assert_called_once_with(
            "requirements.txt",
            transform_with_token="my-token",
            gitlab_domain=None,
            ci_job_token=None,
            github_root_dir=None,
            project_names=None,
        )

    def test_uses_github_token_environment_variable_if_no_token_supplied(self):
        with patch.dict(
            "pip_install_privates.install.os.environ", {"GITHUB_TOKEN": "my-token"}
        ):
            with patch.object(sys, "argv", ["pip-install", "requirements.txt"]):
                install()

        self.mock_collect.assert_called_once_with(
            "requirements.txt",
            transform_with_token="my-token",
            gitlab_domain=None,
            ci_job_token=None,
            github_root_dir=None,
            project_names=None,
        )

    def test_uses_none_if_no_token_supplied_and_no_github_token_defined_as_environment_variable(
        self,
    ):
        with patch.object(sys, "argv", ["pip-install", "requirements.txt"]):
            install()

        self.mock_collect.assert_called_once_with(
            "requirements.txt",
            transform_with_token=None,
            gitlab_domain=None,
            ci_job_token=None,
            github_root_dir=None,
            project_names=None,
        )

    def test_commandline_requires_requirements_file(self):
        with patch("sys.stderr", new_callable=StringIO):
            with patch.object(sys, "argv", ["pip-install"]):
                self.assertRaises(SystemExit, install)

    def test_calls_pip_with_install_and_collected_requirements(self):
        self.mock_collect.return_value = ["req1", "req2"]

        with patch.object(sys, "argv", ["pip-install", "requirements.txt"]):
            install()

        self.mock_pip.assert_called_once_with(["install", "req1", "req2"])

    def test_raises_error_if_pip_fails(self):
        self.mock_pip.return_value = status_codes.ERROR

        with patch.object(sys, "argv", ["pip-install", "requirements.txt"]):
            self.assertRaises(RuntimeError, install)

    def test_uses_both_gitlab_domain_and_token_environment_variables_if_defined(self):
        with patch.dict(
            "pip_install_privates.install.os.environ",
            {
                "GITLAB_DOMAIN": "my.gitlab.com",
                "GITHUB_TOKEN": "my-token",
                "CI_JOB_TOKEN": "CI-token",
            },
        ):
            with patch.object(sys, "argv", ["pip-install", "requirements.txt"]):
                install()

        self.mock_collect.assert_called_once_with(
            "requirements.txt",
            transform_with_token="my-token",
            gitlab_domain="my.gitlab.com",
            ci_job_token="CI-token",
            github_root_dir=None,
            project_names=None,
        )

    def test_uses_gitlab_domain_environment_variable_if_defined(self):
        with patch.dict(
            "pip_install_privates.install.os.environ",
            {"GITLAB_DOMAIN": "my.gitlab.com", "CI_JOB_TOKEN": "CI-token"},
        ):
            with patch.object(sys, "argv", ["pip-install", "requirements.txt"]):
                install()

        self.mock_collect.assert_called_once_with(
            "requirements.txt",
            transform_with_token=None,
            gitlab_domain="my.gitlab.com",
            ci_job_token="CI-token",
            github_root_dir=None,
            project_names=None,
        )

    def test_commandline_with_all_arguments(self):
        with patch.dict(
            "pip_install_privates.install.os.environ",
            {
                "CI_JOB_TOKEN": "env_ci_job_token",
                "GITLAB_DOMAIN": "env.gitlab.com",
                "GITHUB_ROOT_DIR": "env_github_root_dir",
                "PROJECT_NAMES": "env_project1,env_project2",
            },
        ):
            with patch.object(
                sys,
                "argv",
                [
                    "pip-install",
                    "--gitlab-token",
                    "arg_ci_job_token",
                    "--gitlab-domain",
                    "arg.gitlab.com",
                    "--github-root-dir",
                    "arg_github_root_dir",
                    "--project-names",
                    "arg_project1,arg_project2",
                    "requirements/development.txt",
                ],
            ):
                install()

        self.mock_collect.assert_called_once_with(
            "requirements/development.txt",
            transform_with_token=None,
            gitlab_domain="arg.gitlab.com",
            ci_job_token="arg_ci_job_token",
            github_root_dir="arg_github_root_dir",
            project_names="arg_project1,arg_project2",
        )
