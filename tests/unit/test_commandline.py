try:
    # python 2
    from StringIO import StringIO
except ImportError:
    # python 3
    from io import StringIO

from unittest import TestCase

import sys
from mock import patch
from pip.status_codes import ERROR, SUCCESS

from pipprivates.install import install


class TestCommandLine(TestCase):

    def setUp(self):
        collect_patcher = patch('pipprivates.install.collect_requirements')
        self.addCleanup(collect_patcher.stop)
        self.mock_collect = collect_patcher.start()

        pip_patcher = patch('pip.main')
        self.addCleanup(pip_patcher.stop)
        self.mock_pip = pip_patcher.start()
        self.mock_pip.return_value = SUCCESS

    def test_commandline_passes_requirements_file_to_collect(self):
        with patch.object(sys, 'argv', ['pip-install', 'requirements.txt']):
            install()

        self.mock_collect.assert_called_once_with('requirements.txt',
                                                  transform_with_token=None)

    def test_commandline_passes_specified_token_to_collect(self):
        with patch.object(sys, 'argv',
                          ['pip-install', '-t', 'my-token', 'requirements.txt']):
            install()

        self.mock_collect.assert_called_once_with('requirements.txt',
                                                  transform_with_token='my-token')

    def test_commandline_requires_requirements_file(self):
        with patch('sys.stderr', new_callable=StringIO):
            with patch.object(sys, 'argv', ['pip-install']):
                self.assertRaises(SystemExit, install)

    def test_calls_pip_with_install_and_collected_requirements(self):
        self.mock_collect.return_value = ['req1', 'req2']

        with patch.object(sys, 'argv', ['pip-install', 'requirements.txt']):
            install()

        self.mock_pip.assert_called_once_with(['install', 'req1', 'req2'])

    def test_raises_error_if_pip_fails(self):
        self.mock_pip.return_value = ERROR

        with patch.object(sys, 'argv', ['pip-install', 'requirements.txt']):
            self.assertRaises(RuntimeError, install)
