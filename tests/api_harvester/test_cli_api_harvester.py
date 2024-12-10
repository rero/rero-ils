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

"""Test api harvester cli."""

import json
from os.path import dirname, join

import mock
from click.testing import CliRunner
from utils import mock_response

from rero_ils.modules.api_harvester.cli import (
    add_api_source_config,
    harvest,
    info,
    init_api_harvest_config,
    set_last_run,
)
from rero_ils.modules.documents.api import Document
from rero_ils.modules.holdings.api import Holding


def test_cli(app, org_sion, lib_sion, loc_online_sion, item_type_online_sion):
    """Test count cli."""
    runner = CliRunner()

    config_file = join(dirname(__file__), "../data/apisources.yml")
    result = runner.invoke(init_api_harvest_config, [config_file])
    assert result.exit_code == 0
    output = result.output.strip().split("\n")
    assert output[0] == "ApiHarvestConfig NJ-CANTOOK: Add"
    assert output[1] == "ApiHarvestConfig VS-CANTOOK: Add"

    result = runner.invoke(info)
    assert result.exit_code == 0
    output = result.output.strip().split("\n")
    assert output == [
        "NJ-CANTOOK",
        "\tlastrun   : 1900-01-01 00:00:00",
        "\turl       : https://bm.ebibliomedia.ch",
        "\tclassname : rero_ils.modules.api_harvester.cantook.api.ApiCantook",
        "\tcode   : ebibliomedia",
        "VS-CANTOOK",
        "\tlastrun   : 1900-01-01 00:00:00",
        "\turl       : https://mediatheque-valais.cantookstation.eu",
        "\tclassname : rero_ils.modules.api_harvester.cantook.api.ApiCantook",
        "\tcode   : mv-cantook",
    ]

    result = runner.invoke(set_last_run, ["NJ-CANTOOK", "-d", "2002-02-02"])
    assert result.exit_code == 0
    output = result.output.strip().split("\n")
    assert output == ["Set last run NJ-CANTOOK: 2002-02-02"]

    result = runner.invoke(info)
    assert result.exit_code == 0
    output = result.output.strip().split("\n")
    assert output == [
        "NJ-CANTOOK",
        "\tlastrun   : 2002-02-02 00:00:00",
        "\turl       : https://bm.ebibliomedia.ch",
        "\tclassname : rero_ils.modules.api_harvester.cantook.api.ApiCantook",
        "\tcode   : ebibliomedia",
        "VS-CANTOOK",
        "\tlastrun   : 1900-01-01 00:00:00",
        "\turl       : https://mediatheque-valais.cantookstation.eu",
        "\tclassname : rero_ils.modules.api_harvester.cantook.api.ApiCantook",
        "\tcode   : mv-cantook",
    ]

    result = runner.invoke(
        add_api_source_config, ["NJ-CANTOOK", "-c", "ebibliomedia-test", "-u"]
    )
    assert result.exit_code == 0
    output = result.output.strip().split("\n")
    assert output == ["ApiHarvestConfig NJ-CANTOOK: Update code:ebibliomedia-test"]

    result = runner.invoke(info)
    assert result.exit_code == 0
    output = result.output.strip().split("\n")
    assert output == [
        "NJ-CANTOOK",
        "\tlastrun   : 2002-02-02 00:00:00",
        "\turl       : https://bm.ebibliomedia.ch",
        "\tclassname : rero_ils.modules.api_harvester.cantook.api.ApiCantook",
        "\tcode   : ebibliomedia-test",
        "VS-CANTOOK",
        "\tlastrun   : 1900-01-01 00:00:00",
        "\turl       : https://mediatheque-valais.cantookstation.eu",
        "\tclassname : rero_ils.modules.api_harvester.cantook.api.ApiCantook",
        "\tcode   : mv-cantook",
    ]

    # test harvest with create
    content = json.load(open(join(dirname(__file__), "../data/mv_cantook.json")))
    headers_1 = {
        "X-Total-Pages": 1,
        "X-Total-Items": len(content.get("resources", [])),
        "X-Current-Page": 1,
    }
    mock_response_1 = mock_response(json_data=content, headers=headers_1)
    headers_2 = {
        "X-Total-Pages": 1,
        "X-Total-Items": len(content.get("resources", [])),
        "X-Current-Page": 2,
    }
    mock_response_2 = mock_response(json_data={"resources": []}, headers=headers_2)
    with mock.patch(
        "requests.Session.get",
        side_effect=[mock_response_1, mock_response_2],
    ):
        result = runner.invoke(harvest, ["-n", "VS-CANTOOK", "-v"])
        assert result.exit_code == 0
        output = result.output.strip().split("\n")
        print(output)
        assert output == [
            "Harvest api: VS-CANTOOK",
            "API page: 1 url: "
            "https://mediatheque-valais.cantookstation.eu/v1/resources.json?start_at=1900-01-01T00:00:00&page=1",
            "1: CANTOOK:mv-cantook cantook-immateriel.frO1109367 = CREATED",
            "2: CANTOOK:mv-cantook cantook-immateriel.frO1097420 = CREATED",
            "3: CANTOOK:mv-cantook cantook-feedhttps-www-feedbooks-com-item-6177668 = CREATED",
            "API harvest VS-CANTOOK items=3 | got=3 new=3 updated=0 deleted=0",
        ]
        assert Document.count() == 3
        assert Holding.count() == 3

    # test harvest with update and delete
    runner.invoke(set_last_run, ["VS-CANTOOK", "-d", "1900-01-01"])
    content = json.load(
        open(join(dirname(__file__), "../data/mv_cantook_deleted.json"))
    )
    headers_1 = {
        "X-Total-Pages": 1,
        "X-Total-Items": len(content.get("resources", [])),
        "X-Current-Page": 1,
    }
    mock_response_1 = mock_response(json_data=content, headers=headers_1)
    with mock.patch(
        "requests.Session.get",
        side_effect=[mock_response_1, mock_response_2],
    ):
        result = runner.invoke(harvest, ["-n", "VS-CANTOOK", "-v"])
        assert result.exit_code == 0
        output = result.output.strip().split("\n")
        print(output)
        assert output == [
            "Harvest api: VS-CANTOOK",
            "API page: 1 url: "
            "https://mediatheque-valais.cantookstation.eu/v1/resources.json?start_at=1900-01-01T00:00:00&page=1",
            "1: CANTOOK:mv-cantook cantook-immateriel.frO1109367 = DELETED",
            "2: CANTOOK:mv-cantook cantook-immateriel.frO1097420 = UPDATED",
            "3: CANTOOK:mv-cantook cantook-feedhttps-www-feedbooks-com-item-6177668 = DELETED",
            "API harvest VS-CANTOOK items=3 | got=3 new=0 updated=1 deleted=2",
        ]
        assert Document.count() == 1
        assert Holding.count() == 1
