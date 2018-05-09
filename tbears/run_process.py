# -*- coding: utf-8 -*-
# Copyright 2017-2018 theloop Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import requests

from .util import post, make_json_payload
from .sub_process import SubProcess
requests.packages.urllib3.disable_warnings()


class RunProcess(object):
    __PYTHON_VERSION = 'python'
    __TBEARS_ROOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
    __FLASK_SERVER_PATH = os.path.join(__TBEARS_ROOT_PATH, 'tools/test.py')

    def __init__(self):
        self.__sub_process = None

    def run(self, project_name: str):
        if self.__sub_process is None or not self.__sub_process.is_run():
            process_args = [self.__PYTHON_VERSION, self.__FLASK_SERVER_PATH]
            print(process_args)
            self.__sub_process = SubProcess(process_args)

        self.install_request(project_name)

    def stop(self):
        if self.__sub_process:
            self.__sub_process.stop()

    @staticmethod
    def install_request(project: str):
        """ Request install score.

        :param project: Project directory name.
        """
        url = "http://localhost:"
        project_dict = make_json_payload(project)
        post(url, project_dict)
