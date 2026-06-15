# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utilities about acquisition accounts."""


def sort_accounts_as_tree(accounts):
    """Sort a list of acquisition account as a hierarchical tree.

    :param accounts: the accounts to sort.
    :return: the same account list sorted as a hierarchical tree.
    """

    def sort_by_name_key(acc):
        return acc.get("name")

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
