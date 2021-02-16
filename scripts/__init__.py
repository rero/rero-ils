# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Poetry script utils."""

import os
# import subprocess
import sys

# def __getattr__(name):  # python 3.7+, otherwise define each script manually
#     name = name.replace('_', '-')
#     subprocess.run(
#         ['python', '-u', '-m', name] + sys.argv[1:]
#     )  # run whatever you like based on 'name'


def run(prg_name, *args):  # python 3.7+, otherwise define each script manually
    def fn():
        # Replace current Python program by prg_name (same PID)
        os.execvp(prg_name, [prg_name] + list(args) + sys.argv[1:])
    return fn
