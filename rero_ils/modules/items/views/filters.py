# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Jinja filters."""


def issue_client_reference(issue_data):
    """Build the best possible client reference for an issue.

    :param issue_data: the dict containing holding client reference.
    :returns: the string representing the client reference.
    :rtype: str
    """
    if holding_data := issue_data.get("holdings"):
        parts = list(
            filter(
                None,
                [holding_data.get("client_id"), holding_data.get("order_reference")],
            )
        )
        return f"({'/'.join(parts)})" if parts else ""
    return None
