# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Utilities about acquisition accounts."""


def sort_accounts_as_tree(accounts):
    """Sort a list of acquisition account as a hierarchical tree.

    :param accounts: the accounts to sort.
    :return: the same account list sorted as a hierarchical tree.
    """
    def sort_by_name_key(acc):
        return acc.get('name')

    def _get_children_account(acc):
        children = filter(lambda a: a.parent_pid == acc.pid, accounts)
        return sorted(children, key=sort_by_name_key)

    def _build_tree(accounts_parts):
        tree = []
        for acc in sorted(accounts_parts, key=sort_by_name_key):
            tree.append(acc)
            tree.extend(_build_tree(_get_children_account(acc)))
        return tree

    return _build_tree([a for a in accounts if a.is_root])
