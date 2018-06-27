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


class TbearsBaseException(Exception):
    """Base exception for tbears."""
    pass


class TBearsWriteFileException(TbearsBaseException):
    """Error while write file."""
    pass


class TBearsDeleteTreeException(TbearsBaseException):
    """Error while write file."""
    pass


class TbearsConfigFileException(TbearsBaseException):
    """Error while load deploy config file"""
    pass


class KeyStoreException(TbearsBaseException):
    pass
