# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021-2024 RERO
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

"""Migration Record tests."""

from copy import deepcopy

from rero_ils.modules.deduplications.api import Deduplication
from rero_ils.modules.documents.api import Document, DocumentsSearch


def test_deduplications_documents(app, dedup_doc_data):
    """Test the deduplication for documents."""
    document_data = dedup_doc_data
    dedup = Deduplication()
    assert dedup.get_candidates(deepcopy(document_data)) == []
    doc = Document.create(
        data=deepcopy(document_data), delete_pid=True, dbcommit=True, reindex=True
    )
    DocumentsSearch.flush_and_refresh()
    [(pid, _, score, _)] = dedup.get_candidates(deepcopy(document_data))
    assert (pid, score) == (doc.pid, 1.0)

    # ======= harvested ========
    doc["harvested"] = True
    doc.replace(doc, True, True, True)
    assert dedup.get_candidates(deepcopy(document_data)) == []

    # ======= masked ========
    doc["harvested"] = False
    doc["_masked"] = True
    doc.replace(doc, True, True, True)
    assert dedup.get_candidates(deepcopy(document_data)) == []

    # ======= provisionActivity ========
    doc["_masked"] = False
    doc["provisionActivity"][0]["startDate"] = 1900
    doc.replace(doc, True, True, True)
    [(pid, _, score, _)] = dedup.get_candidates(deepcopy(document_data))
    assert pid == doc.pid
    assert score < 0.9

    doc["provisionActivity"] = [
        {"type": "bf:Production", "startDate": 1970},
        {"type": "bf:Publication", "startDate": 1971},
    ]
    doc.replace(doc, True, True, True)
    [(pid, _, score, _)] = dedup.get_candidates(deepcopy(document_data))
    assert (pid, score) == (doc.pid, 1.0)

    # same date but different type
    doc["provisionActivity"] = [
        {"type": "bf:Production", "startDate": 1971},
        {"type": "bf:Publication", "startDate": 1970},
    ]
    doc.replace(doc, True, True, True)
    [(pid, _, score, _)] = dedup.get_candidates(deepcopy(document_data))
    assert pid == doc.pid
    assert score < 0.9

    doc["provisionActivity"] = deepcopy(document_data["provisionActivity"])
    doc.replace(doc, True, True, True)

    # ======= responsibilityStatement ========
    doc["responsibilityStatement"] = [[{"value": "foo"}]]
    doc.replace(doc, True, True, True)
    [(pid, _, score, _)] = dedup.get_candidates(deepcopy(document_data))
    assert pid == doc.pid
    assert score < 0.95

    doc["responsibilityStatement"] = deepcopy(document_data["responsibilityStatement"])
    doc["responsibilityStatement"][0].insert(0, {"value": "foo"})
    doc.replace(doc, True, True, True)
    [(pid, _, score, _)] = dedup.get_candidates(deepcopy(document_data))
    assert pid == doc.pid
    assert score < 0.95

    doc["responsibilityStatement"] = deepcopy(document_data["responsibilityStatement"])
    doc["responsibilityStatement"][0].append({"value": "foo"})
    doc.replace(doc, True, True, True)
    [(pid, _, score, _)] = dedup.get_candidates(deepcopy(document_data))
    assert (pid, score) == (doc.pid, 1.0)

    # ============== text query ===============
    # reset the data
    doc["responsibilityStatement"] = deepcopy(document_data["responsibilityStatement"])
    doc.replace(doc, True, True, True)

    candidates = dedup.get_candidates(deepcopy(document_data))
    assert candidates[0][0] == doc.pid
    assert candidates[0][2] > 0

    doc.delete(dbcommit=True, delindex=True)
