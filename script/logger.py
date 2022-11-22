#!/usr/bin/env python3
#
# Copyright Rivtower Technologies LLC.
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

import logging
import sys
# 创建日志器logger并将其日志级别设置为DEBUG
logger = logging.getLogger("test_logger")
logger.setLevel(logging.DEBUG)
# 创建一个流处理器handler并将其日志级别设置为DEBUG
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
# 创建一个格式化器formatter并将其添加到处理器handler中
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
# 为日志器logger添加上面创建好的处理器handler
logger.addHandler(handler)
