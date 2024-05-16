import unittest

# Import the function for testing
from pip_install_privates.install import convert_to_gitlab_url_with_token

class TestGitLabURLConversion(unittest.TestCase):
    def test_convert_to_gitlab_url_with_token(self):
        url = 'git+ssh://git@gitlab.test.domain.site/group/test-name.git'
        token = 'dummy_token'
        gitlab_domain = 'gitlab.test.domain.site'
        expected = 'git+https://gitlab-ci-token:dummy_token@gitlab.test.domain.site/group/test-name.git'
        result = convert_to_gitlab_url_with_token(url, token, gitlab_domain)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
