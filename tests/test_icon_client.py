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

import unittest
import os
import socket


from tbears.command.command import Command
from tbears.libs.icon_client import IconClient
from tbears.config.tbears_config import tbears_config
from iconcommons.icon_config import IconConfig
from tests.test_util import TEST_UTIL_DIRECTORY

from tbears.tbears_exception import IconClientException

class TestIconClient(unittest.TestCase):
    def setUp(self):
        self.cmd = Command()
        tbears_config_path = os.path.join(TEST_UTIL_DIRECTORY, 'test_tbears.json')
        self.conf = IconConfig(tbears_config_path, tbears_config)
        self.conf.load()
        self.conf['config'] = tbears_config_path
        self.cmd.cmdServer.start(self.conf)

        # Check server started (before test Icon client, sever has to be started)
        self.assertTrue(self.check_server())

    def check_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # if socket is connected, the result code is 0 (false).
        result = sock.connect_ex(('127.0.0.1', 9000))
        sock.close()
        return result == 0

    def tearDown(self):
        self.cmd.cmdServer.stop(self.conf)

    def test_send_request_to_server(self):
        # Correct request
        payload = {"jsonrpc": "2.0", "method": "icx_getTotalSupply", "id": 111}
        client = IconClient('http://127.0.0.1:9000/api/v3')
        response = client.send(payload)
        #check get response correctly, don't check the response data
        self.assertEqual(200, response.status_code)

        # Incorrect request: input url which is omitted port number
        payload = {"jsonrpc": "2.0", "method": "icx_getTotalSupply", "id": 111}
        client = IconClient('http://127.0.0.1:/api/v3')
        response = client.send(payload)
        # check get response correctly, don't check the response data
        self.assertEqual(404, response.status_code)

        # Bad request: invalid payload data (nonexistent method name)
        incorrect_payload = {"jsonrpc": "2.0", "method": "icx_invalid_requests", "id": 111}
        client = IconClient('http://127.0.0.1:9000/api/v3')
        response = client.send(incorrect_payload)
        print(400, response.status_code)

        # Bad request: insufficient payload data (method is not set)
        insufficient_payload = {"jsonrpc": "2.0", "id": 111}
        client = IconClient('http://127.0.0.1:9000/api/v3')
        response = client.send(insufficient_payload)
        print(400, response.text)

        # requests when server stopped
        self.cmd.cmdServer.stop(self.conf)
        payload = {"jsonrpc": "2.0", "method": "icx_getTotalSupply", "id": 111}
        client = IconClient('http://127.0.0.1:9000/api/v3')
        self.assertRaises(IconClientException, client.send, payload )




