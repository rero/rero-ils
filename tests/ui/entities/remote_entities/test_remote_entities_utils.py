# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Entities Record utils."""

from unittest import mock

import pytest
from requests import RequestException

from rero_ils.modules.entities.remote_entities.utils import get_mef_data_by_type
from tests.utils import mock_response


@mock.patch("requests.Session.get")
def test_utils_mef_data(mock_get, app):
    """."""
    with pytest.raises(KeyError):
        get_mef_data_by_type("idref", "pid", "dummy_entity", verbose=True)

    mock_get.return_value = mock_response(json_data={"hits": {"hits": [], "toto": "foo"}})
    with pytest.raises(ValueError):
        get_mef_data_by_type("viaf", "pid", "agents", verbose=True)

    mock_get.return_value = mock_response(status=400, json_data={"error": "Bad request"})
    with pytest.raises(RequestException):
        get_mef_data_by_type("viaf", "pid", "agents", verbose=True)
