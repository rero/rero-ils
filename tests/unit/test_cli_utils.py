# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test cli."""

from os.path import dirname, join

from click.testing import CliRunner

from rero_ils.modules.cli.documents import (
    create_documents_with_items_lofis_cli,
    validate_documents_with_items_lofis_cli,
)
from rero_ils.modules.cli.utils import (
    check_validate,
    extract_from_xml,
    has_spdx_header,
    needs_spdx_header,
    token_create,
)


def test_cli_validate(app):
    """Test validate cli."""
    runner = CliRunner()
    file_name = join(dirname(__file__), "../data/documents.json")

    res = runner.invoke(check_validate, [file_name, "doc", "-v"])
    assert res.output.strip().split("\n") == [
        f"Testing json schema for file: {file_name} type: doc",
        "\tTest record: 1",
        "\tTest record: 2",
    ]


def test_cli_access_token(app, patron_martigny):
    """Test access token cli."""
    runner = CliRunner()
    res = runner.invoke(
        token_create,
        ["-n", "test", "-u", patron_martigny.dumps().get("email"), "-t", "my_token"],
    )
    assert res.output.strip().split("\n") == ["my_token"]


def test_cli_extract_from_xml(app, tmpdir, document_marcxml):
    """Test extract from xml cli."""
    pids_path = join(dirname(__file__), "..", "data", "001.pids")
    xml_path = join(dirname(__file__), "..", "data", "xml", "documents.xml")
    temp_file_name = join(tmpdir, "temp.xml")
    runner = CliRunner()
    result = runner.invoke(extract_from_xml, [pids_path, xml_path, temp_file_name, "-v"])
    assert result.exit_code == 0
    results_output = result.output.split("\n")
    assert results_output[0] == "Extract pids from xml: "
    assert results_output[4] == "Search pids count: 1"


def test_cli_validate_documents_items_lofi(app, loc_public_martigny):
    """Test validate documents with items lofis cli."""
    runner = CliRunner()
    file_name = join(dirname(__file__), "../data/documents_items_lofi.json")

    res = runner.invoke(validate_documents_with_items_lofis_cli, [file_name, "-v"])
    assert res.output.strip().split("\n")[1:] == [
        "1          document: dummy_1 errors: 1",
        "    documents: 'type' is a required property",
        "2          document: dummy_2 OK",
        "3          document: dummy_3 errors: 1",
        "    items: 1 No 'location' in item",
        "4          document: dummy_4 errors: 1",
        "    local_fields: doc lofi: 1 'fields' is a required property",
        "5          document: dummy_5 OK",
        "6          document: dummy_6 OK",
        "7          document: dummy_7 errors: 1",
        "    local_fields: item: 1 lofi: 1 'fields' is a required property",
        "8          document: dummy_8 OK",
        "Errors: 4",
    ]


def test_cli_create_documents_items_lofi(app, loc_public_martigny, item_type_standard_martigny):
    """Test create documents with items lofis cli."""
    runner = CliRunner()
    file_name = join(dirname(__file__), "../data/documents_items_lofi.json")

    res = runner.invoke(create_documents_with_items_lofis_cli, [file_name, "-v", "-o", "-c"])
    assert res.output.strip().split("\n")[1:] == [
        "1          doc: ???",
        "    documents: 'type' is a required property",
        "2          doc: 2",
        "3          doc: 3",
        "    items: No 'location' in item",
        "4          doc: 4",
        "    local_fields: 'fields' is a required property",
        "5          doc: 5 lofis: 2",
        "6          doc: 6 items: 1",
        "7          doc: 7 items: 2",
        "    local_fields: 'fields' is a required property",
        "8          doc: 8 items: 3 lofis: 4",
        "Document count: 8",
        "documents",
        "    ok    : 7",
        "    errors: 1",
        "items",
        "    ok    : 3",
        "    errors: 1",
        "local_fields",
        "    ok    : 2",
        "    errors: 2",
    ]


def test_cli_needs_spdx_header(tmp_path):
    """Test the selection of the files requiring a license header."""
    (script := tmp_path / "server").write_text("#!/usr/bin/env bash\necho\n")
    (plain := tmp_path / "LICENSE").write_text("GNU AFFERO GENERAL PUBLIC LICENSE\n")

    assert needs_spdx_header("rero_ils/modules/cli/utils.py")
    assert needs_spdx_header("docker/nginx/Dockerfile")
    assert needs_spdx_header(str(script))
    assert not needs_spdx_header(str(plain))
    assert not needs_spdx_header("tests/data/documents.json")
    assert not needs_spdx_header("rero_ils/modules/notifications/templates/email/at_desk/eng.txt")
    assert not needs_spdx_header(".github/workflows/release.yml")


def test_cli_has_spdx_header(tmp_path):
    """Test the detection of the license header."""
    copyright_tag = "SPDX-FileCopyrightText: Fondation RERO+"
    license_tag = "SPDX-License-Identifier: AGPL-3.0-or-later"

    def write(name, content):
        (file_path := tmp_path / name).write_text(content)
        return str(file_path)

    assert has_spdx_header(write("api.py", f"# {copyright_tag}\n# {license_tag}\n"))
    assert has_spdx_header(write("page.html", f"{{# {copyright_tag} #}}\n{{# {license_tag} #}}\n"))
    assert has_spdx_header(write("README.md", f"<!--\n{copyright_tag}\n{license_tag}\n-->\n"))
    # missing tag, wrong license and header pushed out of the first lines
    assert not has_spdx_header(write("no_license.py", f"# {copyright_tag}\n"))
    assert not has_spdx_header(write("wrong_license.py", f"# {copyright_tag}\n# SPDX-License-Identifier: MIT\n"))
    assert not has_spdx_header(write("too_late.py", f"{'\n' * 5}# {copyright_tag}\n# {license_tag}\n"))
