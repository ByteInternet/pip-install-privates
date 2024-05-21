import os
import tempfile
from unittest import TestCase
from unittest.mock import patch

from pip_install_privates.install import collect_requirements


class TestInstall(TestCase):

    def _create_reqs_file(self, reqs):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write("\n".join(reqs).encode("utf-8"))

        self.addCleanup(os.unlink, f.name)
        return f.name

    def test_considers_all_requirements_in_file(self):
        fname = self._create_reqs_file(["mock==2.0.0", "nose==1.3.7", "fso==0.3.1"])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ["mock==2.0.0", "nose==1.3.7", "fso==0.3.1"])

    def test_removes_comments(self):
        fname = self._create_reqs_file(
            ["mock==2.0.0", "# for testing", "nose==1.3.7", "fso==0.3.1"]
        )

        ret = collect_requirements(fname)
        self.assertEqual(ret, ["mock==2.0.0", "nose==1.3.7", "fso==0.3.1"])

    def test_removes_trailing_comments(self):
        fname = self._create_reqs_file(
            ["mock==2.0.0", "nose==1.3.7 # for testing", "fso==0.3.1"]
        )

        ret = collect_requirements(fname)
        self.assertEqual(ret, ["mock==2.0.0", "nose==1.3.7", "fso==0.3.1"])

    def test_skips_empty_lines(self):
        fname = self._create_reqs_file(
            ["mock==2.0.0", "", "nose==1.3.7", "", "fso==0.3.1"]
        )

        ret = collect_requirements(fname)
        self.assertEqual(ret, ["mock==2.0.0", "nose==1.3.7", "fso==0.3.1"])

    def test_strips_whitespaces(self):
        fname = self._create_reqs_file(["  mock==2.0.0  ", "  ", "nose==1.3.7  "])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ["mock==2.0.0", "nose==1.3.7"])

    def test_reads_included_files(self):
        basename = self._create_reqs_file(["mock==2.0.0", "nose==1.3.7"])
        fname = self._create_reqs_file(["-r {}".format(basename), "fso==0.3.1"])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ["mock==2.0.0", "nose==1.3.7", "fso==0.3.1"])

    def test_reads_chain_of_included_files(self):
        file1 = self._create_reqs_file(["mock==2.0.0", "nose==1.3.7"])
        file2 = self._create_reqs_file(["-r {}".format(file1), "Django==1.10"])
        file3 = self._create_reqs_file(
            ["amqp==1.4.7", "-r {}".format(file2), "six==1.10.0"]
        )
        file4 = self._create_reqs_file(["-r {}".format(file3), "fso==0.3.1"])

        ret = collect_requirements(file4)
        self.assertEqual(
            ret,
            [
                "amqp==1.4.7",
                "mock==2.0.0",
                "nose==1.3.7",
                "Django==1.10",
                "six==1.10.0",
                "fso==0.3.1",
            ],
        )

    def test_honors_vcs_urls(self):
        fname = self._create_reqs_file(["git+https://github.com/ByteInternet/..."])

        ret = collect_requirements(fname)
        self.assertEqual(ret, ["git+https://github.com/ByteInternet/..."])

    def test_transforms_vcs_git_url_to_oauth(self):
        fname = self._create_reqs_file(["git+git@github.com:ByteInternet/..."])

        ret = collect_requirements(fname, transform_with_token="my-token")
        self.assertEqual(
            ret, ["git+https://my-token:x-oauth-basic@github.com/ByteInternet/..."]
        )

    def test_transforms_vcs_git_url_to_oauth_dashe_option(self):
        fname = self._create_reqs_file(["-e git+git@github.com:ByteInternet/..."])

        ret = collect_requirements(fname, transform_with_token="my-token")
        self.assertEqual(
            ret,
            ["-e", "git+https://my-token:x-oauth-basic@github.com/ByteInternet/..."],
        )

    def test_transforms_vcs_ssh_url_to_oauth(self):
        fname = self._create_reqs_file(["git+ssh://git@github.com/ByteInternet/..."])

        ret = collect_requirements(fname, transform_with_token="my-token")
        self.assertEqual(
            ret, ["git+https://my-token:x-oauth-basic@github.com/ByteInternet/..."]
        )

    def test_transforms_vcs_ssh_url_to_oauth_dashe_option(self):
        fname = self._create_reqs_file(["-e git+ssh://git@github.com/ByteInternet/..."])

        ret = collect_requirements(fname, transform_with_token="my-token")
        self.assertEqual(
            ret,
            ["-e", "git+https://my-token:x-oauth-basic@github.com/ByteInternet/..."],
        )

    def test_transforms_urls_in_included_files(self):
        file1 = self._create_reqs_file(
            ["mock==2.0.0", "-e git+git@github.com:ByteInternet/...", "nose==1.3.7"]
        )
        fname = self._create_reqs_file(["-r {}".format(file1), "fso==0.3.1"])

        ret = collect_requirements(fname, transform_with_token="my-token")
        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                "git+https://my-token:x-oauth-basic@github.com/ByteInternet/...",
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_git_plus_git_urls_to_regular_url_if_no_token_provided(self):
        file1 = self._create_reqs_file(
            ["mock==2.0.0", "-e git+git@github.com:ByteInternet/...", "nose==1.3.7"]
        )
        fname = self._create_reqs_file(["-r {}".format(file1), "fso==0.3.1"])

        ret = collect_requirements(fname)
        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                "git+https://github.com/ByteInternet/...",
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_git_plus_ssh_urls_to_regular_url_if_no_token_provided(self):
        file1 = self._create_reqs_file(
            [
                "mock==2.0.0",
                "-e git+ssh://git@github.com/ByteInternet/...",
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file1), "fso==0.3.1"])

        ret = collect_requirements(fname)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                "git+https://github.com/ByteInternet/...",
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_git_plus_https_urls_to_https_url_with_oauth_token_if_token_provided(
        self,
    ):
        file1 = self._create_reqs_file(
            ["mock==2.0.0", "git+https://github.com/ByteInternet/...", "nose==1.3.7"]
        )
        fname = self._create_reqs_file(["-r {}".format(file1), "fso==0.3.1"])

        ret = collect_requirements(fname, transform_with_token="my-token")

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "git+https://my-token:x-oauth-basic@github.com/ByteInternet/...",
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_editable_git_plus_https_urls_to_editable_https_url_with_oauth_token_if_token_provided(
        self,
    ):
        file1 = self._create_reqs_file(
            ["mock==2.0.0", "-e git+https://github.com/ByteInternet/...", "nose==1.3.7"]
        )
        fname = self._create_reqs_file(["-r {}".format(file1), "fso==0.3.1"])

        ret = collect_requirements(fname, transform_with_token="my-token")

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                "git+https://my-token:x-oauth-basic@github.com/ByteInternet/...",
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_does_not_transform_git_plus_https_urls_to_https_url_with_oauth_token_if_no_token_provided(
        self,
    ):
        file1 = self._create_reqs_file(
            ["mock==2.0.0", "-e git+https://github.com/ByteInternet/...", "nose==1.3.7"]
        )
        fname = self._create_reqs_file(["-r {}".format(file1), "fso==0.3.1"])

        ret = collect_requirements(fname)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                "git+https://github.com/ByteInternet/...",
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_editable_requirement_with_pip_environment_marker_to_github_url_with_token(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                "-e 'git+https://github.com/ByteInternet/... ; python_version==\"2.7\"'",
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname, transform_with_token=True)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                'git+https://True:x-oauth-basic@github.com/ByteInternet/... ; python_version=="2.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_editable_requirement_with_pip_environment_marker_inline_comment_to_github_url_with_token(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                "-e 'git+https://github.com/ByteInternet/... ; python_version==\"2.7\"'  # We need this because reasons",
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname, transform_with_token=True)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                'git+https://True:x-oauth-basic@github.com/ByteInternet/... ; python_version=="2.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_editable_requirement_with_pip_environment_marker_to_github_url_without_token(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                "-e 'git+https://github.com/ByteInternet/... ; python_version==\"2.7\"'",
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                'git+https://github.com/ByteInternet/... ; python_version=="2.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_editable_requirement_with_pip_environment_marker_inline_comment_to_github_url_no_token(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                "-e 'git+https://github.com/ByteInternet/... ; python_version==\"2.7\"'  # We need this because reasons",
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                'git+https://github.com/ByteInternet/... ; python_version=="2.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_editable_requirement_with_pip_environment_marker_if_cannot_convert_to_url(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                "-e 'banana+https://github.com/ByteInternet/... ; python_version==\"2.7\"'",
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                'banana+https://github.com/ByteInternet/... ; python_version=="2.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_editable_requirement_with_pip_environment_marker_inline_comment_if_cannot_convert_to_url(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                "-e 'banana+https://github.com/ByteInternet/... ; python_version==\"2.7\"'  # We need this because reasons",
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                'banana+https://github.com/ByteInternet/... ; python_version=="2.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_requirement_if_pip_environment_marker_in_tokens(self):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                'myrequirement==1.3.3.7 ; python_version=="3.7"',
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                'myrequirement==1.3.3.7 ; python_version=="3.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_requirement_if_pip_environment_marker_in_tokens_with_inline_comment(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                'myrequirement==1.3.3.7 ; python_version=="3.7"  # We need this because reasons',
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                'myrequirement==1.3.3.7 ; python_version=="3.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_non_editable_github_url_with_pip_environment_markers_to_correct_requirement(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                'git+ssh://git@github.com/ByteInternet/... ; python_version=="3.7"',
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                'git+https://github.com/ByteInternet/... ; python_version=="3.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_non_editable_github_url_with_pip_environment_markers_to_correct_requirement_with_token(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                'git+ssh://git@github.com/ByteInternet/... ; python_version=="3.7"',
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname, transform_with_token=True)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                'git+https://True:x-oauth-basic@github.com/ByteInternet/... ; python_version=="3.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_non_editable_github_url_with_pip_environment_markers_to_correct_requirement_with_comment(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                'git+ssh://git@github.com/ByteInternet/... ; python_version=="3.7"  # We need this',
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                'git+https://github.com/ByteInternet/... ; python_version=="3.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_non_editable_github_url_with_pip_environment_markers_to_correct_requirement_with_token_and_comment(
        self,
    ):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                'git+ssh://git@github.com/ByteInternet/... ; python_version=="3.7"  # We need this because reasons',
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        ret = collect_requirements(fname, transform_with_token=True)

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                'git+https://True:x-oauth-basic@github.com/ByteInternet/... ; python_version=="3.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_gitlab_url_to_oauth(self):
        fname = self._create_reqs_file(["git+ssh://git@group.test/project.git@v1.0"])

        with patch.dict("os.environ", {"CI_JOB_TOKEN": "gitlab-token"}):
            ret = collect_requirements(
                fname, gitlab_domain="group.test", ci_job_token="gitlab-token"
            )

        self.assertEqual(
            ret,
            ["git+https://gitlab-ci-token:gitlab-token@group.test/project.git@v1.0"],
        )

    def test_transforms_gitlab_git_url_to_oauth(self):
        fname = self._create_reqs_file(["git+git@group.test:project.git@v1.0"])

        with patch.dict("os.environ", {"CI_JOB_TOKEN": "gitlab-token"}):
            ret = collect_requirements(
                fname, gitlab_domain="group.test", ci_job_token="gitlab-token"
            )

        self.assertEqual(
            ret,
            ["git+https://gitlab-ci-token:gitlab-token@group.test/project.git@v1.0"],
        )

    def test_transforms_gitlab_https_url_to_oauth(self):
        fname = self._create_reqs_file(["git+https://group.test/project.git@v1.0"])

        with patch.dict("os.environ", {"CI_JOB_TOKEN": "gitlab-token"}):
            ret = collect_requirements(
                fname, gitlab_domain="group.test", ci_job_token="gitlab-token"
            )

        self.assertEqual(
            ret,
            ["git+https://gitlab-ci-token:gitlab-token@group.test/project.git@v1.0"],
        )

    def test_transforms_gitlab_url_included_files(self):
        file1 = self._create_reqs_file(
            ["mock==2.0.0", "git+ssh://git@group.test/project.git@v1.0", "nose==1.3.7"]
        )
        fname = self._create_reqs_file(["-r {}".format(file1), "fso==0.3.1"])

        with patch.dict("os.environ", {"CI_JOB_TOKEN": "gitlab-token"}):
            ret = collect_requirements(
                fname, gitlab_domain="group.test", ci_job_token="gitlab-token"
            )

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "git+https://gitlab-ci-token:gitlab-token@group.test/project.git@v1.0",
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )

    def test_transforms_gitlab_git_url_with_environment_marker(self):
        file = self._create_reqs_file(
            [
                "mock==2.0.0",
                "-e 'git+ssh://git@group.test/project.git@v1.0 ; python_version==\"2.7\"'",
                "nose==1.3.7",
            ]
        )
        fname = self._create_reqs_file(["-r {}".format(file), "fso==0.3.1"])

        with patch.dict("os.environ", {"CI_JOB_TOKEN": "gitlab-token"}):
            ret = collect_requirements(
                fname, gitlab_domain="group.test", ci_job_token="gitlab-token"
            )

        self.assertEqual(
            ret,
            [
                "mock==2.0.0",
                "-e",
                'git+https://gitlab-ci-token:gitlab-token@group.test/project.git@v1.0 ; python_version=="2.7"',
                "nose==1.3.7",
                "fso==0.3.1",
            ],
        )
