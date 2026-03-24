# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Entities Record tests."""

import tempfile
from copy import deepcopy
from unittest import mock

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.entities.remote_entities.api import (
    RemoteEntitiesSearch,
    RemoteEntity,
    remote_entity_id_fetcher,
)
from rero_ils.modules.entities.remote_entities.replace import ReplaceIdentifiedBy
from rero_ils.modules.entities.remote_entities.sync import SyncEntity
from tests.utils import mock_response


def test_remote_entity_create(app, entity_person_data_tmp, caplog):
    """Test MEF entity creation."""
    pers = RemoteEntity.get_record_by_pid("1")
    assert not pers
    pers = RemoteEntity.create(entity_person_data_tmp, dbcommit=True, delete_pid=True)
    assert pers == entity_person_data_tmp
    assert pers.get("pid") == "1"

    pers = RemoteEntity.get_record_by_pid("1")
    assert pers == entity_person_data_tmp

    fetched_pid = remote_entity_id_fetcher(pers.id, pers)
    assert fetched_pid.pid_value == "1"
    assert fetched_pid.pid_type == "rement"
    entity_person_data_tmp["viaf_pid"] = "1234"
    RemoteEntity.create(entity_person_data_tmp, dbcommit=True, delete_pid=True)
    pers = RemoteEntity.get_record_by_pid("2")
    assert pers.get("viaf_pid") == "1234"

    assert pers.organisation_pids == []

    pers.delete_from_index()
    # test the messages from current_app.logger
    assert caplog.records[0].name == "opensearch"
    assert caplog.record_tuples[1] == (
        "invenio",
        30,
        "Cannot delete from index RemoteEntity: 2",
    )


@mock.patch("requests.Session.get")
def test_remote_entity_mef_create(
    mock_contributions_mef_get,
    app,
    mef_agents_url,
    entity_person_data_tmp,
    entity_person_response_data,
):
    """Test MEF contribution creation."""
    count = RemoteEntity.count()
    mock_contributions_mef_get.return_value = mock_response(json_data=entity_person_response_data)
    pers_mef, online = RemoteEntity.get_record_by_ref(f"{mef_agents_url}/rero/A017671081")
    RemoteEntitiesSearch.flush_and_refresh()
    assert pers_mef == entity_person_data_tmp
    assert online
    assert RemoteEntity.count() == count + 1
    pers_mef.pop("idref")
    pers_mef["sources"] = ["gnd"]
    pers_mef.replace(pers_mef, dbcommit=True)
    pers_db, online = RemoteEntity.get_record_by_ref(f"{mef_agents_url}/gnd/13343771X")
    assert pers_db["sources"] == ["gnd"]
    assert not online
    # remove created contribution
    RemoteEntity.get_record_by_pid(entity_person_data_tmp["pid"]).delete(True, True, True)


@mock.patch("requests.Session.get")
def test_sync_contribution(mock_get, app, mef_agents_url, entity_person_data_tmp, document_data_ref):
    """Test MEF agent synchronization."""
    # === setup
    log_path = tempfile.mkdtemp()
    sync_entity = SyncEntity(log_dir=log_path)
    assert sync_entity

    pers = RemoteEntity.create(entity_person_data_tmp, dbcommit=True, reindex=True, delete_pid=True)
    RemoteEntitiesSearch.flush_and_refresh()

    idref_pid = pers["idref"]["pid"]
    document_data_ref["contribution"][0]["entity"]["$ref"] = f"{mef_agents_url}/idref/{idref_pid}"

    doc = Document.create(deepcopy(document_data_ref), dbcommit=True, reindex=True, delete_pid=True)
    DocumentsSearch.flush_and_refresh()

    # Test that entity could not be deleted
    assert pers.get_links_to_me(True)["documents"] == [doc.pid]
    assert pers.reasons_not_to_delete()["links"]["documents"] == 1

    # === nothing to update
    sync_entity._get_latest = mock.MagicMock(return_value=entity_person_data_tmp)
    # nothing touched as it is up-to-date
    assert (0, 0, set()) == sync_entity.sync(f"{pers.pid}")
    # nothing removed
    assert sync_entity.remove_unused(f"{pers.pid}") == (0, [])

    # === MEF metadata has been changed
    data = deepcopy(entity_person_data_tmp)
    data["idref"]["authorized_access_point"] = "foo"
    sync_entity._get_latest = mock.MagicMock(return_value=data)
    mock_resp = {"hits": {"hits": [{"id": data["pid"], "metadata": data}]}}
    mock_get.return_value = mock_response(json_data=mock_resp)
    assert DocumentsSearch().query("term", contribution__entity__authorized_access_point_fr="foo").count() == 0
    # synchronization the same document has been updated 3 times, one MEF
    # record has been updated, no errors
    assert (1, 1, set()) == sync_entity.sync(f"{pers.pid}")
    DocumentsSearch.flush_and_refresh()

    # contribution and document should be changed
    assert RemoteEntity.get_record_by_pid(pers.pid)["idref"]["authorized_access_point"] == "foo"
    assert DocumentsSearch().query("term", contribution__entity__authorized_access_point_fr="foo").count()
    # nothing has been removed as only metadata has been changed
    assert sync_entity.remove_unused(f"{pers.pid}") == (0, [])

    # === a new MEF exists with the same content
    data = deepcopy(entity_person_data_tmp)
    # MEF pid has changed
    data["pid"] = "foo_mef"
    # mock MEF services
    sync_entity._get_latest = mock.MagicMock(return_value=data)
    mock_resp = {"hits": {"hits": [{"id": data["pid"], "metadata": data}]}}
    mock_get.return_value = mock_response(json_data=mock_resp)

    # synchronization the same document has been updated 3 times, one MEF
    # record has been updated, no errors
    assert (1, 1, set()) == sync_entity.sync(f"{pers.pid}")
    DocumentsSearch.flush_and_refresh()
    # new contribution has been created
    assert RemoteEntity.get_record_by_pid("foo_mef")
    assert RemoteEntity.get_record_by_ref(f"{mef_agents_url}/idref/{idref_pid}")[0]
    db_agent = Document.get_record_by_pid(doc.pid).get("contribution")[0]["entity"]
    assert db_agent["pid"] == "foo_mef"
    # the old MEF has been removed
    assert sync_entity.remove_unused(f"{pers.pid}") == (1, [])
    # should not exists anymore
    assert not RemoteEntity.get_record_by_pid(pers.pid)

    # === Update the MEF links content
    data = deepcopy(entity_person_data_tmp)
    # MEF pid has changed
    data["pid"] = "foo_mef"
    # IDREF pid has changed
    data["idref"]["pid"] = "foo_idref"
    # mock MEF services
    sync_entity._get_latest = mock.MagicMock(return_value=data)
    mock_resp = {"hits": {"hits": [{"id": data["pid"], "metadata": data}]}}
    mock_get.return_value = mock_response(json_data=mock_resp)

    # synchronization the same document has been updated 3 times,
    # one MEF record has been updated, no errors
    assert (1, 1, set()) == sync_entity.sync(f"{data['pid']}")
    DocumentsSearch.flush_and_refresh()
    # new contribution has been created
    assert RemoteEntity.get_record_by_pid("foo_mef")
    # document has been updated with the new MEF and IDREF pid
    assert DocumentsSearch().query("term", contribution__entity__pids__remote="foo_mef").count()
    assert DocumentsSearch().query("term", contribution__entity__pids__idref="foo_idref").count()
    db_agent = Document.get_record_by_pid(doc.pid).get("contribution")[0]["entity"]
    assert db_agent["$ref"] == f"{mef_agents_url}/idref/foo_idref"
    assert db_agent["pid"] == "foo_mef"

    # remove the document
    doc = Document.get_record_by_pid(doc.pid)
    doc.delete(True, True, True)
    DocumentsSearch.flush_and_refresh()

    # the MEF record can be removed
    assert sync_entity.remove_unused() == (1, [])
    # should not exists anymore
    assert not RemoteEntity.get_record_by_pid("foo_mef")


@mock.patch("requests.Session.get")
def test_sync_concept(mock_get, app, mef_concepts_url, entity_topic_data, document_data_subject_ref):
    """Test MEF agent synchronization."""
    # === setup
    log_path = tempfile.mkdtemp()
    sync_entity = SyncEntity(log_dir=log_path)
    assert sync_entity

    topic = RemoteEntity.create(entity_topic_data, dbcommit=True, reindex=True, delete_pid=True)
    RemoteEntitiesSearch.flush_and_refresh()

    entity_url = f"{mef_concepts_url}/idref/{topic['idref']['pid']}"
    document_data_subject_ref["subjects"][0]["entity"]["$ref"] = entity_url

    doc = Document.create(
        deepcopy(document_data_subject_ref),
        dbcommit=True,
        reindex=True,
        delete_pid=True,
    )
    DocumentsSearch.flush_and_refresh()

    # === nothing to update
    sync_entity._get_latest = mock.MagicMock(return_value=entity_topic_data)
    # nothing touched as it is up-to-date
    assert (0, 0, set()) == sync_entity.sync(f"pid:{topic.pid}")
    # nothing removed
    assert sync_entity.remove_unused(f"pid:{topic.pid}") == (0, [])

    # === MEF metadata has been changed
    data = deepcopy(entity_topic_data)
    data["idref"]["authorized_access_point"] = "foo"
    sync_entity._get_latest = mock.MagicMock(return_value=data)
    mock_resp = {"hits": {"hits": [{"id": data["pid"], "metadata": data}]}}
    mock_get.return_value = mock_response(json_data=mock_resp)
    assert DocumentsSearch().query("term", subjects__entity__authorized_access_point_fr="foo").count() == 0
    # synchronization the same document has been updated 3 times, one MEF
    # record has been updated, no errors
    assert (1, 1, set()) == sync_entity.sync(f"pid:{topic.pid}")
    DocumentsSearch.flush_and_refresh()

    # contribution and document should be changed
    entity = RemoteEntity.get_record_by_pid(topic.pid)
    assert entity["idref"]["authorized_access_point"] == "foo"
    assert DocumentsSearch().query("term", subjects__entity__authorized_access_point_fr="foo").count()
    # nothing has been removed as only metadata has been changed
    assert sync_entity.remove_unused(topic.pid) == (0, [])

    # RESET FIXTURES
    #  * Remove the document
    #  * Entity record can be removed ; and should not exist anymore
    doc = Document.get_record_by_pid(doc.pid)
    doc.delete(True, True, True)
    DocumentsSearch.flush_and_refresh()
    assert sync_entity.remove_unused() == (1, [])
    assert not RemoteEntity.get_record_by_pid("foo_mef")


def test_remote_entity_properties(entity_person, item_lib_martigny, document, document_data, mef_concept1):
    """Test entity properties."""
    item = item_lib_martigny

    assert document.pid not in entity_person.documents_pids()
    assert str(document.id) not in entity_person.documents_ids()
    assert item.organisation_pid not in entity_person.organisation_pids
    document["contribution"] = [
        {
            "entity": {
                "$ref": "https://mef.rero.ch/api/agents/idref/223977268",
            },
            "role": ["cre"],
        }
    ]
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid in entity_person.documents_pids()
    assert str(document.id) in entity_person.documents_ids()
    assert item.organisation_pid in entity_person.organisation_pids

    assert entity_person == RemoteEntity.get_entity("mef", entity_person.pid)
    assert entity_person == RemoteEntity.get_entity("viaf", "70119347")

    sources_pids = entity_person.source_pids()
    assert sources_pids["idref"] == "223977268"
    assert sources_pids["gnd"] == "13343771X"
    assert sources_pids["rero"] == "A017671081"

    # Test special behavior of `get_record_by_ref` ::
    #   Simulate an exception into the entity creation to test the exception
    #   catching block statement.
    with mock.patch(
        "rero_ils.modules.entities.remote_entities.api.RemoteEntity.create",
        side_effect=Exception(),
    ):
        entity, _ = RemoteEntity.get_record_by_ref("https://bib.rero.ch/api/documents/dummy_doc")
        assert entity is None

    # remove contribution
    document.pop("contribution")
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid not in entity_person.documents_pids()
    assert str(document.id) not in entity_person.documents_ids()
    assert item.organisation_pid not in entity_person.organisation_pids

    # add subjects
    document["subjects"] = [
        {
            "entity": {
                "$ref": "https://mef.rero.ch/api/concepts/idref/ent_concept_idref",
            }
        }
    ]
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid in mef_concept1.documents_pids()
    assert str(document.id) in mef_concept1.documents_ids()
    assert item.organisation_pid in mef_concept1.organisation_pids
    # remove subjects
    document.pop("subjects")
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid not in mef_concept1.documents_pids()
    assert str(document.id) not in mef_concept1.documents_ids()
    assert item.organisation_pid not in mef_concept1.organisation_pids

    # add genreForm
    document["genreForm"] = [
        {
            "entity": {
                "$ref": "https://mef.rero.ch/api/concepts/idref/ent_concept_idref",
            }
        }
    ]
    document.update(document, dbcommit=True, reindex=True)
    assert document.pid in mef_concept1.documents_pids()
    assert str(document.id) in mef_concept1.documents_ids()
    assert item.organisation_pid in mef_concept1.organisation_pids

    # Reset fixture
    document.update(document_data, dbcommit=True, reindex=True)


def test_replace_identified_by(
    app,
    entity_organisation,
    entity_person_rero,
    person2_data,
    entity_person_all,
    entity_topic_data_2,
    entity_topic_data_temporal,
    entity_place_data,
    document,
    document_sion_items,
    export_document,
):
    """Test replace identified by with $ref."""
    # === setup
    log_path = tempfile.mkdtemp()
    replace_identified_by = ReplaceIdentifiedBy(field="contribution", verbose=True, dry_run=False, log_dir=log_path)
    assert replace_identified_by
    assert replace_identified_by.count() == 2

    # no MEF response for agents in contribution
    with mock.patch(
        "requests.Session.get",
        side_effect=[mock_response(status=404), mock_response(status=404)],
    ):
        changed, not_found, rero_only = replace_identified_by.run()
        assert changed == 0
        assert not_found == 2
        assert rero_only == 0
        assert replace_identified_by.not_found == {
            "bf:Organisation": {"gnd:1161956409": "Convegno internazionale di italianistica Craiova"},
            "bf:Person": {"rero:A003633163": "Nebehay, Christian Michael"},
        }
        replace_identified_by.set_timestamp()
        data = replace_identified_by.get_timestamp()
        assert "contribution" in data
        assert data["contribution"]["changed"] == 0
        assert data["contribution"]["not found"] == 2
        assert data["contribution"]["rero only"] == 0

    # with MEF response for agents in contribution
    with mock.patch(
        "requests.Session.get",
        side_effect=[
            mock_response(json_data=entity_person_rero),
            mock_response(json_data=entity_organisation),
        ],
    ):
        changed, not_found, rero_only = replace_identified_by.run()
        assert changed == 1
        assert not_found == 0
        assert rero_only == 1
        assert replace_identified_by.rero_only == {"bf:Person": {"rero:A003633163": "Nebehay, Christian Michael"}}
    # with MEF response for concepts in subjects
    replace_identified_by = ReplaceIdentifiedBy(field="subjects", verbose=True, dry_run=False, log_dir=log_path)
    assert replace_identified_by
    assert replace_identified_by.count() == 2
    with mock.patch(
        "requests.Session.get",
        side_effect=[
            mock_response(json_data=entity_person_all),
            mock_response(json_data=entity_topic_data_temporal),
            mock_response(json_data=entity_place_data),
            mock_response(json_data=person2_data),
            mock_response(
                json_data={
                    "rero": {
                        "authorized_access_point": "Europe occidentale",
                        "type": "bf:Place",
                    }
                }
            ),
            mock_response(json_data=entity_topic_data_2),
        ],
    ):
        # bf:Work has no MEF family at all: no MEF lookup is attempted for it, it's just not_found
        changed, not_found, rero_only = replace_identified_by.run()
        assert changed == 1
        assert not_found == 1
        assert rero_only == 3
        assert dict(sorted(replace_identified_by.rero_only.items())) == {
            "bf:Person": {"rero:A009963344": "Athenagoras (patriarche oecuménique ; 1)"},
            "bf:Topic": {"rero:A021039750": "Bases de données déductives"},
            "bf:Place": {"rero:A009975209": "Europe occidentale"},
        }
        assert replace_identified_by.not_found == {
            "bf:Work": {"rero:A001234567": "Bases de donnéesi (Voltenauer, Marc)"}
        }


def test_replace_identified_by_type_mismatch(app, entity_organisation, entity_organisation_data):
    """A MEF type differing from the document should not block the $ref replace.

    The identifier alone is enough to link the entity. Only for
    `contribution` is the mismatch still flagged for the metadata admin.
    """
    log_path = tempfile.mkdtemp()
    entity = {
        "entity": {
            "type": "bf:Person",
            "authorized_access_point": "Some person",
            "identifiedBy": {"type": "GND", "value": "1161956409"},
        }
    }

    # subjects/genreForm: replaced, mismatch is not flagged
    replace_identified_by = ReplaceIdentifiedBy(field="subjects", verbose=True, dry_run=False, log_dir=log_path)
    with mock.patch("requests.Session.get", side_effect=[mock_response(json_data=entity_organisation_data)]):
        changed = replace_identified_by._do_entity(deepcopy(entity), "doc_pid_test")
    assert changed is True
    assert replace_identified_by.rero_only == {}

    # contribution: replaced, but mismatch is flagged for the metadata admin
    replace_identified_by = ReplaceIdentifiedBy(field="contribution", verbose=True, dry_run=False, log_dir=log_path)
    contribution_entity = deepcopy(entity)
    with mock.patch("requests.Session.get", side_effect=[mock_response(json_data=entity_organisation_data)]):
        changed = replace_identified_by._do_entity(contribution_entity, "doc_pid_test")
    assert changed is True
    assert contribution_entity["entity"]["$ref"] == "https://mef.rero.ch/api/agents/gnd/1161956409"
    assert replace_identified_by.rero_only == {}
    assert replace_identified_by.type_mismatch == {
        "bf:Person": {
            "gnd:1161956409": 'bf:Person != bf:Organisation : "Convegno internazionale di italianistica Craiova"'
        }
    }


def test_replace_identified_by_type_mismatch_does_not_block_retry(app, entity_organisation, entity_organisation_data):
    """A type-mismatch flag on one document must not block replacement for another.

    `type_mismatch` (flagged for admin review) must stay independent from
    `rero_only` (which also gates retries): a successfully replaced entity
    must not silently block a later document sharing the same identifier.
    """
    log_path = tempfile.mkdtemp()
    replace_identified_by = ReplaceIdentifiedBy(field="contribution", verbose=True, dry_run=False, log_dir=log_path)

    def make_entity():
        return {
            "entity": {
                "type": "bf:Person",
                "authorized_access_point": "Some person",
                "identifiedBy": {"type": "GND", "value": "1161956409"},
            }
        }

    entity_doc1 = make_entity()
    with mock.patch("requests.Session.get", side_effect=[mock_response(json_data=entity_organisation_data)]):
        changed_doc1 = replace_identified_by._do_entity(entity_doc1, "doc_pid_1")
    assert changed_doc1 is True
    assert entity_doc1["entity"]["$ref"] == "https://mef.rero.ch/api/agents/gnd/1161956409"

    # a second document sharing the same identifier must still be replaced,
    # not skipped because the first one was already flagged in type_mismatch
    entity_doc2 = make_entity()
    with mock.patch("requests.Session.get", side_effect=[mock_response(json_data=entity_organisation_data)]):
        changed_doc2 = replace_identified_by._do_entity(entity_doc2, "doc_pid_2")
    assert changed_doc2 is True
    assert entity_doc2["entity"]["$ref"] == "https://mef.rero.ch/api/agents/gnd/1161956409"


def test_replace_identified_by_type_not_allowed(app):
    """A resolved MEF type invalid for the field is logged as error and not linked.

    Unlike a Person/Organisation mismatch (still linked, flagged as warning), a
    resolved type that cannot appear in the field at all (e.g. a contribution
    resolving to a bf:Topic) must be refused: no $ref is written.
    """
    log_path = tempfile.mkdtemp()
    entity = {
        "entity": {
            "type": "bf:Person",
            "authorized_access_point": "Some person",
            "identifiedBy": {"type": "GND", "value": "1161956409"},
        }
    }
    # The identifier resolves to a bf:Topic, which is not allowed in a contribution.
    mef_data = {
        "pid": "topic1",
        "type": "bf:Topic",
        "gnd": {"pid": "1161956409", "authorized_access_point": "Some topic"},
    }
    original = deepcopy(entity)

    replace_identified_by = ReplaceIdentifiedBy(field="contribution", verbose=True, dry_run=False, log_dir=log_path)
    with mock.patch("requests.Session.get", side_effect=[mock_response(json_data=mef_data)]):
        changed = replace_identified_by._do_entity(entity, "doc_pid_test")

    assert not changed
    # entity left untouched — no $ref written
    assert entity == original
    assert replace_identified_by.type_mismatch == {}
    assert replace_identified_by.type_not_allowed == {
        "bf:Person": {"gnd:1161956409": 'bf:Person -> bf:Topic not allowed for contribution : "Some topic"'}
    }


def test_replace_identified_by_type_not_allowed_gates_retry(app):
    """A type-not-allowed identifier must not be re-queried against MEF.

    The outcome is deterministic per identifier, so a second document sharing
    it is skipped without another MEF call.
    """
    log_path = tempfile.mkdtemp()

    def make_entity():
        return {
            "entity": {
                "type": "bf:Person",
                "authorized_access_point": "Some person",
                "identifiedBy": {"type": "GND", "value": "1161956409"},
            }
        }

    mef_data = {
        "pid": "topic1",
        "type": "bf:Topic",
        "gnd": {"pid": "1161956409", "authorized_access_point": "Some topic"},
    }
    replace_identified_by = ReplaceIdentifiedBy(field="contribution", verbose=True, dry_run=False, log_dir=log_path)

    with mock.patch("requests.Session.get", return_value=mock_response(json_data=mef_data)) as mock_get:
        replace_identified_by._do_entity(make_entity(), "doc_pid_1")
        replace_identified_by._do_entity(make_entity(), "doc_pid_2")

    # the second document is gated by the type_not_allowed cache — MEF hit once
    assert mock_get.call_count == 1


def test_replace_identified_by_timestamp_reports_each_outcome(app):
    """set_timestamp records each outcome under its own key, without conflation.

    `rero only` must not absorb the `type mismatch` count anymore; both, plus
    `type not allowed`, are reported distinctly.
    """
    _SET_TS = "rero_ils.modules.entities.remote_entities.replace.utils_set_timestamp"
    replace = ReplaceIdentifiedBy(field="contribution", verbose=True, dry_run=True, log_dir=tempfile.mkdtemp())
    replace.changed = 5
    replace.not_found = {"bf:Person": {"idref:1": "x"}}
    replace.rero_only = {"bf:Person": {"rero:2": "x"}}
    replace.type_mismatch = {"bf:Person": {"gnd:3": "x"}}
    replace.type_not_allowed = {"bf:Person": {"gnd:4": "x"}}

    with mock.patch(_SET_TS) as mock_set, mock.patch.object(replace, "get_timestamp", return_value={}):
        replace.set_timestamp()

    payload = mock_set.call_args.kwargs["contribution"]
    assert payload["changed"] == 5
    assert payload["not found"] == 1
    assert payload["rero only"] == 1  # does NOT include the type mismatch
    assert payload["type mismatch"] == 1
    assert payload["type not allowed"] == 1


def test_replace_identified_by_query_allowed_types(app):
    """The document search query must use the full per-field allowed-type list.

    `subjects` allows `bf:Work` (it has no MEF family, but is still a valid
    local type per the document schema); a document whose only qualifying
    subject is a `bf:Work` entry must still be selected for scanning.
    `contribution` only allows agents (Person/Organisation): `bf:Work` and
    `bf:Place` must not appear in its filter.
    """
    subjects_types = ReplaceIdentifiedBy(field="subjects").query.to_dict()
    contribution_types = ReplaceIdentifiedBy(field="contribution").query.to_dict()

    def terms_for(query_dict):
        for clause in query_dict["query"]["bool"]["filter"]:
            if "terms" in clause:
                return next(iter(clause["terms"].values()))
        return []

    assert "bf:Work" in terms_for(subjects_types)
    assert "bf:Work" not in terms_for(contribution_types)
    assert "bf:Place" not in terms_for(contribution_types)


def test_replace_identified_by_family_fallback(app, entity_person_all, entity_person_data_all):
    """The MEF family implied by a wrong local type is not the only one tried.

    `subjects` allows agents, concepts and places: if the identifier is not
    found in the family the (here wrong) local type implies, the other
    allowed families are tried before giving up.
    """
    log_path = tempfile.mkdtemp()
    replace_identified_by = ReplaceIdentifiedBy(field="subjects", verbose=True, dry_run=False, log_dir=log_path)
    entity = {
        "entity": {
            "type": "bf:Temporal",
            "authorized_access_point": "Some temporal",
            "identifiedBy": {"type": "RERO", "value": "A003633163"},
        }
    }
    with mock.patch(
        "requests.Session.get",
        side_effect=[mock_response(status=404), mock_response(json_data=entity_person_data_all)],
    ):
        changed = replace_identified_by._do_entity(entity, "doc_pid_test")
    assert changed is True
    assert entity["entity"]["$ref"] == "https://mef.rero.ch/api/agents/idref/029314100"
    assert replace_identified_by.rero_only == {}
    assert replace_identified_by.not_found == {}


def test_entity_get_record_by_ref(mef_agents_url, entity_person, entity_person_data_tmp):
    """Test remote entity: get record by ref."""
    dummy_ref = f"{mef_agents_url}/idref/dummy_idref_pid"
    assert RemoteEntity.get_record_by_ref(dummy_ref) == (None, False)

    # Remote entity from search index
    RemoteEntitiesSearch().filter("term", pid=entity_person.pid).delete()
    RemoteEntitiesSearch.flush_and_refresh()
    ent_ref = f"{mef_agents_url}/idref/{entity_person['idref']['pid']}"
    with mock.patch(
        "rero_ils.modules.entities.remote_entities.api.get_mef_data_by_type",
        return_value=entity_person_data_tmp,
    ):
        entity, online = RemoteEntity.get_record_by_ref(ent_ref)
        assert entity and online
    RemoteEntitiesSearch.flush_and_refresh()
    assert RemoteEntitiesSearch().filter("term", pid=entity_person.pid).count()


def test_remote_entity_resolve(entity_person):
    """Test remote entity resolver."""
    # TODO :: Only for code coverage for now. When relations between entities
    #         will be implemented, this test should be corrected.
    assert entity_person.resolve()
