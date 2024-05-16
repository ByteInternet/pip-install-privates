import unittest
from unittest.mock import patch, mock_open

from pip_install_privates.install import (
    convert_to_gitlab_url_with_token,
    collect_requirements,
    convert_potential_git_url,
)


class TestGitLabURLConversion(unittest.TestCase):

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
        ) as mock_file:
            result = collect_requirements(
                fname, transform_with_token=token, gitlab_domain=gitlab_domain
            )
            self.assertEqual(result, expected)

    def test_convert_potential_git_url(self):
        requirement = "git+ssh://git@gitlab.test.domain.site/group/test-name.git"
        tokens = [requirement]
        token = "dummy_token"
        gitlab_domain = "gitlab.test.domain.site"
        expected = [
            "git+https://gitlab-ci-token:dummy_token@gitlab.test.domain.site/group/test-name.git"
        ]
        result = convert_potential_git_url(
            requirement, tokens, transform_with_token=token, gitlab_domain=gitlab_domain
        )
        self.assertEqual(result, expected)

    def test_collect_requirements_with_multiple_gitlab_urls(self):
        fname = "requirements.txt"
        token = "dummy_token"
        gitlab_domain = "gitlab.test.domain.site"
        requirements = [
            "git+ssh://git@gitlab.test.domain.site/group/test1.git",
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
        ) as mock_file:
            result = collect_requirements(
                fname, transform_with_token=token, gitlab_domain=gitlab_domain
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
        included_data = (
            "git+ssh://git@gitlab.test.domain.site/group/included-test.git\n"
        )
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
                        transform_with_token=token,
                        gitlab_domain=gitlab_domain,
                    )
                    self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
