# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""SRU test fixtures."""

import pytest


@pytest.fixture()
def sru_result_set_client(client):
    """Yield a client with RERO_ILS_SRU_RESULT_SET_TTL set to 60 seconds."""
    client.application.config["RERO_ILS_SRU_RESULT_SET_TTL"] = 60
    yield client
    client.application.config.pop("RERO_ILS_SRU_RESULT_SET_TTL", None)
