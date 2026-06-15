# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test csv creation, import et export."""

import json
from os.path import dirname, join

from click.testing import CliRunner

from rero_ils.modules.cli.fixtures import bulk_load, bulk_save, create_csv


def test_create_csv(app, tmpdir):
    """Test create_csv cli."""
    tmp_dir_name = tmpdir.dirname
    json_file_name = join(dirname(__file__), "../data/documents.json")
    runner = CliRunner()
    result = runner.invoke(create_csv, ["doc", json_file_name, tmp_dir_name, "-l", "-v"])
    assert result.exit_code == 0
    file_name_pidstore = join(tmp_dir_name, "doc_pidstore.csv")
    file_name_metadata = join(tmp_dir_name, "doc_metadata.csv")
    file_name_pids = join(tmp_dir_name, "doc_pids.csv")
    output = result.output.split("\n")
    assert output[0] == f"Create CSV files for: doc from: {json_file_name}"
    assert output[1] == f"\t{file_name_pidstore}"
    assert output[2] == f"\t{file_name_metadata}"
    assert output[3] == f"\t{file_name_pids}"
    assert output[4].split(":")[0] == "1\tdoc\t1"
    assert output[5].split(":")[0] == "2\tdoc\t2"

    result = runner.invoke(bulk_load, ["doc", file_name_metadata, "-r"])
    # assert result.exit_code == 0
    assert result.output.split("\n") == [
        "Load doc CSV files into database.",
        "  Number of records to load: 2",
        f"  Load pids: {file_name_pids}",
        f"  Load pidstore: {file_name_pidstore}",
        f"  Load metatada: {file_name_metadata}",
        "",
    ]
    result = runner.invoke(bulk_save, [tmp_dir_name, "-t", "xxx", "-t", "doc"])
    assert result.exit_code == 0
    assert result.output.split("\n") == [
        "Error xxx does not exist!",
        f"Save doc CSV files to directory: {tmp_dir_name}",
        "Saved records: 2",
        "",
    ]

    saved_name_meta = join(tmp_dir_name, "documents_small_metadata.csv")
    with open(file_name_metadata) as meta, open(saved_name_meta) as saved_meta:
        for line1, line2 in zip(meta, saved_meta):
            line1 = line1.strip().split("\t")[2:]
            json1 = json.loads(line1[1])
            del line1[1]
            line2 = line2.strip().split("\t")[2:]
            json2 = json.loads(line2[1])
            del line2[1]
            assert line1 == line2
            assert json1 == json2

    saved_name_pidstore = join(tmp_dir_name, "documents_small_pidstore.csv")
    with open(file_name_pidstore) as pids, open(saved_name_pidstore) as saved_pidstore:
        for line1, line2 in zip(pids, saved_pidstore):
            line1 = line1.strip().split("\t")[2:]
            line2 = line2.strip().split("\t")[2:]
            assert line1 == line2

    saved_name_pids = join(tmp_dir_name, "documents_small_pids.csv")
    with open(file_name_pids) as pids, open(saved_name_pids) as saved_pids:
        for line1, line2 in zip(pids, saved_pids):
            line1 = line1.strip()
            line2 = line2.strip()
            assert line1 == line2
