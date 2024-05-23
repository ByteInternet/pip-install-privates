import unittest
from unittest.mock import patch, mock_open

from pip_install_privates.install import (
    convert_to_gitlab_url_with_token,
    collect_requirements,
    convert_potential_git_url,
    transform_github_to_gitlab,
)


class TestGitLabURLConversion(unittest.TestCase):

    def setUp(self):
        pip_patcher = patch("pip_install_privates.install.pip_main")
        self.addCleanup(pip_patcher.stop)
        self.mock_pip = pip_patcher.start()
        self.mock_pip.return_value = 0  # status_codes.SUCCESS

    def test_gitlab_and_github_urls_with_tokens(self):
        requirements_content = """
        git+https://${GITLAB_DOMAIN}/web.git@2024egg=hypernode_web_common
        git+https://github.com/test/test.py@20230810-test
        """

        with patch("builtins.open", mock_open(read_data=requirements_content)):
            with patch.dict(
                "os.environ",
                {
                    "GITHUB_TOKEN": "github-token",
                    "CI_JOB_TOKEN": "tokenitself",
                    "GITLAB_DOMAIN": "group.test",
                },
            ):
                collected_requirements = collect_requirements(
                    "requirements.txt",
                    transform_with_token="github-token",
                    gitlab_domain="group.test",
                    ci_job_token="tokenitself",
                )

        expected_gitlab_url = "git+https://gitlab-ci-token:tokenitself@group.test/web.git@2024egg=hypernode_web_common"
        expected_github_url = "git+https://github-token:x-oauth-basic@github.com/test/test.py@20230810-test"

        self.assertIn(expected_gitlab_url, collected_requirements)
        self.assertIn(expected_github_url, collected_requirements)

    def test_convert_to_gitlab_url_with_token(self):
        url = "git+ssh://git@gitlab.test.domain.site/group/test-name.git"
        token = "dummy_token"
        gitlab_domain = "gitlab.test.domain.site"
        expected = "git+https://gitlab-ci-token:dummy_token@gitlab.test.domain.site/group/test-name.git"
        result = convert_to_gitlab_url_with_token(url, token, gitlab_domain)
        self.assertEqual(result, expected)

    def test_collect_requirements_gitlab(self):
        fname = "requirements.txt"
        token = "dummy_token"
        gitlab_domain = "gitlab.test.domain.site"
        expected = [
            "git+https://gitlab-ci-token:dummy_token@gitlab.test.domain.site/group/test-name.git"
        ]

        with patch(
            "builtins.open",
            new_callable=mock_open,
            read_data="git+ssh://git@gitlab.test.domain.site/group/test-name.git\n",
        ):
            result = collect_requirements(
                fname, gitlab_domain=gitlab_domain, ci_job_token=token
            )
            self.assertEqual(result, expected)

    def test_collect_requirements_with_multiple_gitlab_urls(self):
        fname = "requirements.txt"
        token = "dummy_token"
        gitlab_domain = "gitlab.test.domain.site"
        requirements = [
            "git+ssh://git@${GITLAB_DOMAIN}/group/test1.git",
            "git+git@gitlab.test.domain.site:group/test2.git",
            "git+https://gitlab.test.domain.site/group/test3.git",
        ]
        expected = [
            "git+https://gitlab-ci-token:dummy_token@gitlab.test.domain.site/group/test1.git",
            "git+https://gitlab-ci-token:dummy_token@gitlab.test.domain.site/group/test2.git",
            "git+https://gitlab-ci-token:dummy_token@gitlab.test.domain.site/group/test3.git",
        ]

        with patch(
            "builtins.open", new_callable=mock_open, read_data="\n".join(requirements)
        ):
            result = collect_requirements(
                fname, gitlab_domain=gitlab_domain, ci_job_token=token
            )
            self.assertEqual(result, expected)

    def test_convert_potential_git_url_without_token(self):
        requirement = "git+ssh://git@gitlab.test.domain.site/group/test-name.git"
        tokens = [requirement]
        gitlab_domain = "gitlab.test.domain.site"
        expected = ["git+https://gitlab.test.domain.site/group/test-name.git"]
        result = convert_potential_git_url(
            requirement, tokens, gitlab_domain=gitlab_domain
        )
        self.assertEqual(result, expected)

    def test_collect_requirements_with_included_files(self):
        main_reqs = "main_requirements.txt"
        included_reqs = "included_requirements.txt"
        token = "dummy_token"
        gitlab_domain = "gitlab.test.domain.site"
        included_data = "git+ssh://git@${GITLAB_DOMAIN}/group/included-test.git\n"
        main_data = f"-r {included_reqs}\ngit+ssh://git@gitlab.test.domain.site/group/main-test.git\n"
        expected = [
            "git+https://gitlab-ci-token:dummy_token@gitlab.test.domain.site/group/included-test.git",
            "git+https://gitlab-ci-token:dummy_token@gitlab.test.domain.site/group/main-test.git",
        ]

        mock_main_open = mock_open(read_data=main_data)
        mock_included_open = mock_open(read_data=included_data)

        open_mock = mock_open()
        open_mock.side_effect = [
            mock_main_open.return_value,
            mock_included_open.return_value,
        ]

        with patch("builtins.open", open_mock):
            with patch("os.path.abspath", return_value="/path/to"):
                with patch("os.path.dirname", return_value="/path/to"):
                    result = collect_requirements(
                        main_reqs,
                        gitlab_domain=gitlab_domain,
                        ci_job_token=token,
                    )
                    self.assertEqual(result, expected)

    def test_collect_requirements_with_github_url(self):
        fname = "requirements.txt"
        token = "dummy_token"
        requirements = ["git+https://github.com/owner/repo.git"]
        expected = ["git+https://dummy_token:x-oauth-basic@github.com/owner/repo.git"]

        with patch(
            "builtins.open", new_callable=mock_open, read_data="\n".join(requirements)
        ):
            result = collect_requirements(fname, transform_with_token=token)
            self.assertEqual(result, expected)

    def test_collect_requirements_with_multiple_urls(self):
        fname = "requirements.txt"
        gitlab_token = "gitlab_dummy_token"
        github_token = "github_dummy_token"
        gitlab_domain = "gitlab.test.domain.site"
        requirements = [
            "git+ssh://git@gitlab.test.domain.site/group/test1.git",
            "git+https://github.com/owner/repo.git",
        ]
        expected = [
            "git+https://gitlab-ci-token:gitlab_dummy_token@gitlab.test.domain.site/group/test1.git",
            "git+https://github_dummy_token:x-oauth-basic@github.com/owner/repo.git",
        ]

        with patch(
            "builtins.open", new_callable=mock_open, read_data="\n".join(requirements)
        ):
            result = collect_requirements(
                fname,
                gitlab_domain=gitlab_domain,
                ci_job_token=gitlab_token,
                transform_with_token=github_token,
            )
            self.assertEqual(result, expected)

    def test_collect_requirements_with_no_domain_or_token(self):
        fname = "requirements.txt"
        gitlab_token = None
        github_token = "github_dummy_token"
        gitlab_domain = None
        requirements = ["git+https://gitlab.com/owner/repo.git"]
        expected = ["git+https://gitlab.com/owner/repo.git"]

        with patch(
            "builtins.open", new_callable=mock_open, read_data="\n".join(requirements)
        ):
            result = collect_requirements(
                fname,
                gitlab_domain=gitlab_domain,
                ci_job_token=gitlab_token,
                transform_with_token=github_token,
            )
            self.assertEqual(result, expected)

    def test_convert_to_gitlab_with_private_comment(self):
        gitlab_token = "token"
        gitlab_domain = "group.company/root"
        github_root_dir = "ByteInternet"
        requirement = "git+ssh://git@github.com/ByteInternet/my-project.git@my-tag#egg=my_project #pip-private"

        expected = "git+https://gitlab-ci-token:token@group.company/root/my-project.git@my-tag#egg=my_project"

        with patch("builtins.open", new_callable=mock_open, read_data=requirement):
            result = transform_github_to_gitlab(
                line=requirement,
                ci_job_token=gitlab_token,
                gitlab_domain=gitlab_domain,
                github_root_dir=github_root_dir,
            )
            self.assertEqual(result, expected)

    def test_editable_gitlab_url_with_token(self):
        fname = "requirements.txt"
        gitlab_token = "token"
        github_token = None
        gitlab_domain = "group.company/root"
        github_root_dir = "ByteInternet"
        requirements = [
            "git+https://github.com/ByteInternet/my-project.git@my-tag#egg=my_project #pip-private",
        ]
        expected = [
            "git+https://gitlab-ci-token:token@group.company/root/my-project.git@my-tag#egg=my_project",
        ]

        with patch(
            "builtins.open", new_callable=mock_open, read_data="\n".join(requirements)
        ):
            result = collect_requirements(
                fname,
                gitlab_domain=gitlab_domain,
                ci_job_token=gitlab_token,
                transform_with_token=github_token,
                github_root_dir=github_root_dir,
            )
            self.assertEqual(result, expected)
            
    def test_editable_gitlab_url_root_dir_and_ssh(self):
        fname = "requirements.txt"
        gitlab_token = "token"
        github_token = None
        gitlab_domain = "group.company/root"
        github_root_dir = "ByteInternet"
        requirements = [
            "git+ssh://git@github.com/ByteInternet/my-project.git@my-tag#egg=my_project #pip-private",
        ]
        expected = [
            "git+https://gitlab-ci-token:token@group.company/root/my-project.git@my-tag#egg=my_project",
        ]

        with patch(
            "builtins.open", new_callable=mock_open, read_data="\n".join(requirements)
        ):
            result = collect_requirements(
                fname,
                gitlab_domain=gitlab_domain,
                ci_job_token=gitlab_token,
                transform_with_token=github_token,
                github_root_dir=github_root_dir,
            )
            self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
