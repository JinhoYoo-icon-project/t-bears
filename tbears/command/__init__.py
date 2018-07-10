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
import hashlib
import json
import os
import sys
import subprocess
import time
import logging
import socket
from enum import IntEnum

from tbears.util import create_address, get_tbears_config_json
from tbears.util.icx_signer import key_from_key_store, IcxSigner
from tbears.util.libs.icon_client import IconClient
from tbears.util.libs.icon_json import get_icx_sendTransaction_deploy_payload
from ..tbears_exception import TBearsWriteFileException, TBearsDeleteTreeException, TbearsConfigFileException, \
    KeyStoreException, FillDeployPaylodException, IconClientException
from ..util import post, make_install_json_payload, make_exit_json_payload, \
    delete_score_info, get_init_template, get_sample_crowd_sale_contents, get_deploy_config
from ..util import write_file, get_package_json_dict, get_score_main_template

JSON_RPC_SERVER_URL = "http://localhost:9000/api/v3"


class ExitCode(IntEnum):
    SUCCEEDED = 1
    COMMAND_IS_WRONG = 0
    SCORE_PATH_IS_NOT_A_DIRECTORY = 2
    PROJECT_PATH_IS_NOT_EMPTY_DIRECTORY = 3
    WRITE_FILE_ERROR = 4
    DELETE_TREE_ERROR = 5
    SCORE_AlREADY_EXISTS = 6
    PROJECT_AND_CLASS_NAME_EQUAL = 7
    CONFIG_FILE_ERROR = 8
    KEY_STORE_ERROR = 9
    DEPLOY_ERROR = 10
    ICON_CLIENT_ERROR = 11


def init_SCORE(project: str, score_class: str) -> int:
    """Initialize the SCORE.

    :param project: name of SCORE.
    :param score_class: class name of SCORE.
    :return: ExitCode, Succeeded
    """
    if project == score_class:
        print(f'<project> and <score_class> must be different.')
        return ExitCode.PROJECT_AND_CLASS_NAME_EQUAL.value
    if os.path.exists(f"./{project}"):
        logging.debug(f'{project} directory is not empty.')
        return ExitCode.PROJECT_PATH_IS_NOT_EMPTY_DIRECTORY.value

    package_json_dict = get_package_json_dict(project, score_class)
    package_json_contents = json.dumps(package_json_dict, indent=4)
    project_py_contents = get_score_main_template(score_class)
    init_contents = get_init_template(project, score_class)

    try:
        write_file(project, f"{project}.py", project_py_contents)
        write_file(project, "package.json", package_json_contents)
        write_file(project, '__init__.py', init_contents)
        write_file(f'{project}/tests', f'test_{project}.py', '')
        write_file(f'{project}/tests', f'__init__.py', '')
        write_file('./', "tbears.json", get_tbears_config_json())
    except TBearsWriteFileException:
        logging.debug("Except raised while writing files.")
        return ExitCode.WRITE_FILE_ERROR.value

    return ExitCode.SUCCEEDED.value


def run_SCORE(project: str, *options) -> tuple:
    """Run SCORE, embedding SCORE on the server.

    :param project: name of SCORE.
    :param options: install config path or update config path will be given.
    :return: ExitCode, Succeeded
    """
    if os.path.isdir(project) is False:
        print(f'check score path.')
        return ExitCode.SCORE_PATH_IS_NOT_A_DIRECTORY.value, None

    params = {}
    try:
        if options[0]:
            deploy_info = __get_deploy_optional_info(options[1])
            params = deploy_info['params']
    except KeyError:
        print('check your deploy config file')
        return ExitCode.CONFIG_FILE_ERROR.value, None

    if not __is_server_running():
        __start_server()
        time.sleep(2)

    respond = __embed_SCORE_on_server(project, params, options[0])

    return ExitCode.SUCCEEDED.value, respond


def stop_SCORE() -> int:
    """
    Stop score process.
    :return: ExitCode, Succeeded
    """
    while __is_server_running():
        __exit_request()
        # Wait until server socket is released
        time.sleep(2)

    return ExitCode.SUCCEEDED.value


def clear_SCORE() -> int:
    """ Clear score directories (.db, .score)

    :return: ExitCode
    """
    stop_SCORE()

    try:
        delete_score_info()
    except TBearsDeleteTreeException:
        return ExitCode.DELETE_TREE_ERROR.value

    return ExitCode.SUCCEEDED.value


def make_SCORE_samples():
    """Create two score samples (sample_crowdSale, sample_token)

    :return: ExitCode
    """
    tokentest_package_json_dict = get_package_json_dict("sample_token", "SampleToken")
    tokentest_package_json_contents = json.dumps(tokentest_package_json_dict, indent=4)
    tokentest_py_contents = get_score_main_template("SampleToken")
    tokentest_init_contents = get_init_template("sample_token", "SampleToken")

    crowdsale_package_json_dict = get_package_json_dict("sample_crowd_sale", "SampleCrowdSale")
    crowdsale_package_json_contents = json.dumps(crowdsale_package_json_dict, indent=4)
    crowdsale_py_contents = get_sample_crowd_sale_contents()
    crowdsale_init_contents = get_init_template("sample_crowd_sale", "SampleCrowdSale")
    try:
        write_file('./sample_token', 'sample_token.py', tokentest_py_contents)
        write_file('./sample_token', "package.json", tokentest_package_json_contents)
        write_file('./sample_token', '__init__.py', tokentest_init_contents)

        write_file('./sample_crowd_sale', "package.json", crowdsale_package_json_contents)
        write_file('./sample_crowd_sale', '__init__.py', crowdsale_init_contents)
        write_file('./sample_crowd_sale', "sample_crowd_sale.py", crowdsale_py_contents)
        write_file('./', "tbears.json", get_tbears_config_json())

    except TBearsWriteFileException:
        logging.debug("Except raised while writing files.")
        return ExitCode.WRITE_FILE_ERROR.value

    return ExitCode.SUCCEEDED


def deploy_SCORE(project: str, *config_options, key_store_path: str = None, password: str = "",
                 params: dict = {}) -> object:
    """

    :param project: Project which you want to deploy.
    :param config_options: 'install' or 'update' and deploy.json path.
    :param key_store_path: Keystore path. you can get keystore file from icxcli(python package) or
    Icon Wallet(chrome extension)
    :param password: password of keystore file.
    :param params: Parameters passed to the on_init or on_update methods.
    :return:
    """
    try:
        deploy_config = __get_deploy_info()

        private_key = key_from_key_store(key_store_path, password)

        uri = deploy_config['uri']
        step_limit = 5000 if not deploy_config.get('stepLimit', 0) else int(str(deploy_config['stepLimit']), 0)

        score_address = f'cx{"0"*40}'

        if config_options[0] == 'update':
            update_info = __get_deploy_optional_info(config_options[1])
            score_address = update_info['scoreAddress']
            params = update_info['params']
        elif config_options[0] == 'install':
            install_info = __get_deploy_optional_info(config_options[1])
            score_address = f'cx{"0"*40}'
            params = install_info['params']

        icon_client = IconClient(uri)

        deploy_payload = get_icx_sendTransaction_deploy_payload(signer=IcxSigner(private_key), path=project,
                                                                to=score_address, deploy_params=params,
                                                                step_limit=step_limit)

        response = icon_client.send(deploy_payload)

    except TbearsConfigFileException:
        print('Except raised while load your tbears config file.')
        return ExitCode.CONFIG_FILE_ERROR.value, None
    except KeyError:
        print('Except raised while load your tbears config file.')
        return ExitCode.CONFIG_FILE_ERROR.value, None
    except KeyStoreException:
        return ExitCode.KEY_STORE_ERROR.value, None
    except FillDeployPaylodException:
        print('Except raised while zip your score. check your SCORE.')
        return ExitCode.DEPLOY_ERROR.value, None
    except IconClientException:
        print('Timeout happened. Check your internet connection status.')
        return ExitCode.ICON_CLIENT_ERROR.value, None
    else:
        print('result : ', response.json())
        return ExitCode.SUCCEEDED, response


def test_SCORE(project: str) -> int:
    if os.path.isdir(project) is False:
        print(f'check score path.')
        return ExitCode.SCORE_PATH_IS_NOT_A_DIRECTORY.value
    os.chdir(project)
    subprocess.Popen([sys.executable, '-m', 'unittest'])
    time.sleep(1)

    return ExitCode.SUCCEEDED.value


def __start_server():
    logging.debug('start_server() start')

    root_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../'))

    root_path_directory_name = root_path[root_path.rfind('/') + 1:]
    python_module_string = f'{root_path_directory_name}.server.jsonrpc_server'

    # Run jsonrpc_server on background mode
    subprocess.Popen([sys.executable, '-m', python_module_string], close_fds=True)

    logging.debug('start_server() end')


def __embed_SCORE_on_server(project: str, params: dict, deploy_option: str) -> dict:
    """ Request for embedding SCORE on server.
    :param project: Project directory name.
    :param option: install config path or update config path will be given.
    """
    project_dict = make_install_json_payload(project)

    if deploy_option == 'update':
        contract_address = f'cx{create_address(project.encode())}'
        project_dict['params']['to'] = str(contract_address)

    project_dict['params']['data']['params'] = params

    response = post(JSON_RPC_SERVER_URL, project_dict)
    return response


def __exit_request():
    """ Request for exiting SCORE on server.
    """
    project_dict = make_exit_json_payload()
    post(JSON_RPC_SERVER_URL, project_dict)


def __is_server_running():
    """ Check if server is running.
    tbears use 9000 port.
    :return: True means socket is opened.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', 9000))
    sock.close()

    if result:
        logging.debug("socket is closed!")
    else:
        logging.debug("socket is opened!")

    return result is 0


def __get_deploy_optional_info(path: str):
    try:
        with open(path, mode='rb') as param_json:
            contents = param_json.read()
    except IsADirectoryError:
        print(f'{path} is a directory')
        sys.exit(ExitCode.CONFIG_FILE_PATH_IS_WRONG.value)
    except FileNotFoundError:
        print(f'{path} not found.')
        sys.exit(ExitCode.CONFIG_FILE_PATH_IS_WRONG.value)
    except PermissionError:
        print(f'can not access {path}')
        sys.exit(ExitCode.CONFIG_FILE_PATH_IS_WRONG.value)
    else:
        return json.loads(contents)


def __get_deploy_info() -> dict:
    deploy_config = get_deploy_config('./tbears.json')
    return deploy_config
