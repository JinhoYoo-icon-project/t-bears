# Copyright 2018 theloop Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import os
import shutil

from tbears.tbears_exception import TBearsBaseException, TBearsExceptionCode
from tbears.command.command import Command
from tbears.command.command_util import CommandUtil
from tbears.command.command_score import CommandScore
from tbears.tbears_exception import TBearsCommandException
# from tbears.config.tbears_config import TBearsConfig

from tests.test_command_parcing import TestCommand

class TestCommandScore(TestCommand):
    def setUp(self):
        super().setUp()
        self.tearDownParams = {'proj_unittest': 'dir'}

        # need to be checked from the team
        self.project = 'proj_unittest'
        self.uri = 'http://127.0.0.1:9000/api/v3'
        self.arg_type = 'tbears'
        self.mode = "install"
        self.arg_from = "hxaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        self.to = "cx0000000000000000000000000000000000000000"
        self.keystore = './keystore'
        self.config_path = './deploy'

    # Test cli arguments are parced correctly.
    def test_deploy_args_parcing(self):
        # Parsing test
        cmd = f'deploy {self.project} -u {self.uri} -t {self.arg_type} -m {self.mode} -f {self.arg_from} -o {self.to} -k {self.keystore} -c {self.config_path}'
        parsed = self.parser.parse_args(cmd.split())
        self.assertEqual(parsed.command, 'deploy')
        self.assertEqual(parsed.project, self.project)
        self.assertEqual(parsed.uri, self.uri)
        self.assertEqual(parsed.scoreType, self.arg_type)
        self.assertEqual(parsed.mode, self.mode)
        self.assertEqual(parsed.to, self.to)
        self.assertEqual(parsed.keyStore, self.keystore)
        self.assertEqual(parsed.config, self.config_path)

        # Too much argument
        cmd = f'deploy arg1 arg2'
        self.assertRaises(SystemExit, self.parser.parse_args, cmd.split())
        # Leack argument
        cmd = f'deploy'
        self.assertRaises(SystemExit, self.parser.parse_args, cmd.split())
        cmd = f'deploy {self.project} -w wrongoption'
        self.assertRaises(SystemExit, self.parser.parse_args, cmd.split())
        cmd = f'deploy {self.project} -t not_supported_type'
        self.assertRaises(SystemExit, self.parser.parse_args, cmd.split())
        cmd = f'deploy {self.project} -m not_supported_mode'
        self.assertRaises(SystemExit, self.parser.parse_args, cmd.split())
        cmd = f'deploy {self.project} -t icon tbears to_much -t option args'
        self.assertRaises(SystemExit, self.parser.parse_args, cmd.split())
        # Check the specific case of setting deploy

    # Deploy method(deploy, _check_deploy) test. before deploy score,
    # check if arguments satisfy requirements.
    # bug: when test this method in terminal, no error found, but in pycharm Run Test, it raise error
    def test_check_deploy(self):
        project = 'proj_unittest'
        uri = 'http://127.0.0.1:9000/api/v3'
        to = "cx0000000000000000000000000000000000000000"
        keystore = './keystore'

        # # Deploy essential check
        # No project directory
        cmd = f'deploy {project}'
        parsed = self.parser.parse_args(cmd.split())
        self.assertRaises(TBearsCommandException, CommandScore._check_deploy, vars(parsed))

        # make project directory
        os.mkdir(project)

        # # deploy to icon
        # icon type need keystore option
        cmd = f'deploy {project} -t icon'
        parsed = self.parser.parse_args(cmd.split())
        self.assertRaises(TBearsCommandException, CommandScore._check_deploy, vars(parsed))

        # keystore file does not exist
        # sb. 제안: -h에서 keystore file 위치를 입력하라고 명시해주면 좋을 것 같습니다.
        cmd = f'deploy {project} -t icon -k ./no_exist'
        parsed = self.parser.parse_args(cmd.split())
        self.assertRaises(TBearsCommandException, CommandScore._check_deploy, vars(parsed))

        # check return password, actually, after check all requirements, _check_deploy return password
        # this function doesn't vaild password value, just return user's input
        cmd = f'deploy {project} -t icon -k {keystore}'
        user_input_password = "1234"
        parsed = self.parser.parse_args(cmd.split())
        self.assertEqual(CommandScore._check_deploy(vars(parsed), user_input_password), "1234")

        # # deploy to tbears
        # deploy tbears SCORE to remote(doesn't check actual -uri value)
        cmd = f'deploy {project} -t tbears -u http://1.2.3.4:9000/api/v3'
        parsed = self.parser.parse_args(cmd.split())
        self.assertRaises(TBearsCommandException, CommandScore._check_deploy, vars(parsed))

        # check return, as tbears mode doesn't accept user's input, return value always None
        cmd = f'deploy {project} -t tbears'
        parsed = self.parser.parse_args(cmd.split())
        self.assertEqual(CommandScore._check_deploy(vars(parsed)), None)

        # update succecced check

        # update mode need to option
        cmd = f'deploy {project} -m update'
        parsed = self.parser.parse_args(cmd.split())
        self.assertRaises(TBearsCommandException, CommandScore._check_deploy, vars(parsed))

        # delete project directory
        shutil.rmtree(project)

        # check if update mode, to address is vaild, if invaild, raise error
        # Q. is_icon_address_vaild is in iconservice, so should i write testcode for it?

        # check if 'from' address is valid


    def test_deploy(self):
        pass

    def test_clear_args_parcing(self):
        # parsing clear
        cmd = f'clear'
        parsed = self.parser.parse_args(cmd.split())
        self.assertEqual(parsed.command, 'clear')

    def test_clear(self):
        # too much argument
        cmd = f'clear arg1 arg2'
        self.assertRaises(SystemExit, self.parser.parse_args, cmd.split())

