# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""API for deduplications."""

import re

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Q
from Levenshtein import ratio
from unidecode import unidecode

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.documents.dumpers.indexer import IndexerDumper
from rero_ils.modules.documents.extensions.provision_activities import (
    ProvisionActivitiesExtension,
)


class Deduplication(object):
    """Document deduplication class."""

    def __init__(self, es_hosts=[]) -> None:
        """Constructor.

        :param es_hosts: Elasticsearch hosts to search duplicates.
        """
        self.search = self.base_query(es_hosts).source(
            [
                "pid",
                "title",
                "sort_title",
                "sort_date_old",
                "identifiedBy",
                "provisionActivity",
                "responsibilityStatement",
                "type",
            ]
        )

    @classmethod
    def base_query(cls, es_hosts):
        """Elasticsearch base query.

        :param es_hosts: Elasticsearch hosts to search duplicates.
        :returns: Elasticsearch search instance.
        """
        search = DocumentsSearch()
        if es_hosts:
            search = search.using(
                Elasticsearch(
                    hosts=es_hosts,
                    **{"retry_on_timeout": True, "max_retries": 5, "timeout": 20},
                )
            )
        return search.exclude("term", harvested=True).exclude("term", _draft=True)

    def check_date(self, data, candidates):
        """Check dates from the provision activity.

        :param data: the data to import.
        :param candidates: the current candidate list to filter.
        :returns: the filtered candidate list.
        """
        # build a dict with type: date
        prov = {
            p["type"]: p["startDate"]
            for p in data.get("provisionActivity", [])
            if p.get("startDate")
        }
        new_candidates = []
        for candidate in candidates:
            # build a dict with type: date for each candidate
            c_prov = {
                p["type"]: p["startDate"]
                for p in candidate._source.to_dict().get("provisionActivity", [])
                if p.get("startDate")
            }
            # no data in both => keep
            if not c_prov and not prov:
                new_candidates.append(candidate)
            # all common data are equal => keep
            if (prov and c_prov) and (
                prov == {k: c_prov[k] for k in prov.keys() if c_prov.get(k)}
            ):
                new_candidates.append(candidate)
        return new_candidates

    def check_responsibility_statement(self, data, candidates):
        """First author should match.

        :param data: the data to import.
        :param candidates: the current candidate list to filter.
        :returns: the filtered candidate list.
        """
        value = data.get("responsibilityStatement", [])
        new_candidates = []
        for candidate in candidates:
            c_value = candidate._source.to_dict().get("responsibilityStatement", [])
            # keep if both of them are empty
            if not c_value and not value:
                new_candidates.append(candidate)
            # keep if both of them match
            elif (c_value and value) and self.normalize(
                value[0][0]["value"]
            ) == self.normalize(c_value[0][0]["value"]):
                new_candidates.append(candidate)

        return new_candidates

    def check_editor(self, data, candidates):
        """Check dates from the provision activity.

        :param data: the data to import.
        :param candidates: the current candidate list to filter.
        :returns: the filtered candidate list.
        """

        def get_editor(record):
            """Get the normalized editor value."""
            prov = record.get("provisionActivity")
            if not prov:
                return {}
            to_return = set()
            for d in prov[0].get("statement", []):
                if d["type"] == "bf:Agent":
                    for label in d["label"]:
                        to_return.add(self.normalize(label["value"]))
            return to_return

        # build a dict with type: date
        prov = get_editor(data)
        new_candidates = []
        for candidate in candidates:
            # build a dict with type: date for each candidate
            c_prov = get_editor(candidate._source.to_dict())
            if (not prov and not c_prov) or (c_prov == prov):
                new_candidates.append(candidate)
        return new_candidates

    def get_identifiers_candidates(self, data):
        """Get the candidate list based on the identifiers.

        :param data: the data to import.
        """
        # no candidates
        if not data.get("identifiedBy"):
            return []
        # at least one identifier should match
        criteria = Q("match_none")
        for identifier in data["identifiedBy"]:
            criteria |= Q("term", nested_identifiers__type=identifier["type"]) & Q(
                "term", nested_identifiers__value__raw=identifier["value"]
            )
        search = self.search.filter("nested", path="nested_identifiers", query=criteria)

        # should have the same main document type
        if types := [t["main_type"] for t in data["type"]]:
            search = search.filter("terms", type__main_type=types)
        candidates = [hit for hit in search.execute().hits.hits]

        # should match all provision activity dates
        candidates = self.check_date(data, candidates)

        # first author should match
        candidates = self.check_responsibility_statement(data, candidates)

        # editor should correspond
        candidates = self.check_editor(data, candidates)

        # scores are always one if the candidate exists (exact match)
        return [
            (
                hit._source.pid,
                hit._source.to_dict(),
                1.0,
                dict(
                    main_type="1.0",
                    identifier="1.0",
                    reponsibility_statement="1.0",
                    provision_activity="1.0",
                    publication_date="1.0",
                ),
            )
            for hit in candidates
        ]

    @classmethod
    def normalize(cls, value):
        """Normalize a given text value.

        1. map each UTF-8 to the closest ascii value
        2. transform to lower case
        3. remove extra spaces
        :param value: str - a given string.
        :returns: the normalized given value
        """
        return re.sub(r"\s+", " ", unidecode(value).lower().strip())

    def edit_distance(self, text1, text2):
        """Compute a similarity score between two strings.

        Strings are normalized and the score will be normalized between 0 an 1.
        A score < 0.6 is replaced by 0.

        :param text1: str - first string value.
        :param text2: str - second string value.
        :returns: [0.0-1.0] - the score: 1 means a perfect match
        """
        score = ratio(
            self.normalize(text1),
            self.normalize(text2),
        )
        return score if score > 0.6 else 0.0

    def get_title_score(self, data, candidate):
        """Get the title score.

        :returns: the edit distance of the sort title value.
        """
        return self.edit_distance(data["sort_title"], candidate["sort_title"])

    def get_doc_type_score(self, data, candidate):
        """Get the document type score.

        :returns: 1 if at least one main type matched.
        """
        return (
            1.0
            if (
                {t["main_type"] for t in data["type"]}
                & {t["main_type"] for t in candidate["type"]}
            )
            else 0
        )

    def get_publication_date_score(self, data, candidate):
        """Get the document type score.

        :returns: 1 if both exist and are equal matched, None if does not exists.
        """
        publication_date = data.get("sort_date_old")
        c_publication_date = candidate.get("sort_date_old")
        if publication_date and c_publication_date:
            return publication_date == c_publication_date
        else:
            return 0 if bool(publication_date) != bool(c_publication_date) else 1

    def get_provision_activity_score(self, data, candidate):
        """Get the provision activity score.

        :returns: 1 if both exist and are equal matched, 0 otherwise.
        """
        prov_act = data["provisionActivity"][0]["_text"][0]["value"]
        c_prov_act = candidate["provisionActivity"][0]["_text"][0]["value"]
        if prov_act and c_prov_act:
            return self.edit_distance(prov_act, c_prov_act)
        else:
            return 0 if bool(prov_act) != bool(c_prov_act) else 1

    def get_responsibility_score(self, data, candidate):
        """Get the document type score.

        :returns: 1 if both exist and are equal matched.
        """
        resp = data.get("responsibilityStatement")
        c_resp = candidate.get("responsibilityStatement")
        if resp and c_resp:
            return self.edit_distance(resp[0][0]["value"], c_resp[0][0]["value"])
        else:
            return 0 if bool(resp) != bool(c_resp) else 1

    def get_identifier_score(self, data, candidate):
        """Get the document type score.

        :returns: 1 if both exist and are equal matched.
        """
        # identifiers
        identifiers = [
            d for d in data.get("identifiedBy", []) if d["type"] != "bf:Local"
        ]
        c_identifiers = [
            d for d in candidate.get("identifiedBy", []) if d["type"] != "bf:Local"
        ]
        if identifiers and c_identifiers:
            common_ids = {f"{d['type']}-{d['value']}" for d in identifiers} & {
                f"{d['type']}-{d['value']}" for d in c_identifiers
            }
            return 1 if common_ids else 0
        else:
            return 0 if bool(identifiers) != bool(c_identifiers) else 1

    def rescore(self, data, candidate):
        """Compute the score for a given candidate.

        :param data: the data to import.
        :param candidates: the current candidate list to filter.
        :returns: the score and a dict containing some detailed score information.
        """
        # get the candidate data from ES format
        candidate = candidate._source.to_dict()

        scores = dict(
            # title
            title=(
                6.0,
                self.get_title_score(data, candidate),
            ),
            # main type
            main_type=(
                3.0,
                self.get_doc_type_score(data, candidate),
            ),
            publication_date=(
                5.0,
                self.get_publication_date_score(data, candidate),
            ),
            provision_activity=(
                3.0,
                self.get_provision_activity_score(data, candidate),
            ),
            reponsibility_statement=(
                2.0,
                self.get_responsibility_score(data, candidate),
            ),
            identifier=(3.0, self.get_identifier_score(data, candidate)),
        )
        # filter None score
        scores = {k: v for k, v in scores.items() if v[1] is not None}
        detailed_scores = {k: f"({v[1]:.2f})^{v[0]}" for k, v in scores.items()}
        # combine the scores
        return (
            sum([weight * score for (weight, score) in scores.values()])
            / sum([weight for (weight, _) in scores.values()]),
            detailed_scores,
        )

    def get_text_candidates(self, data):
        """Get candidates using text queries (fuzzy search).

        :param data: the data to import.
        :returns: the list of the candidate.
        """
        # build the text query
        # use the sort_title field as it contains the normalized title
        title = data["sort_title"]

        data_text = [title]
        if respState := data.get("responsibilityStatement"):
            data_text.append(respState[0][0]["value"])
        if prov := data.get("provisionActivity"):
            data_text.append(prov[0]["_text"][0]["value"])
        data_text = " ".join(data_text)

        # phrase search on the title
        query = Q(
            "simple_query_string",
            query=f'"{title}"',
            fields=["title._text"],
            default_operator="AND",
            flags="PHRASE|WHITESPACE",
            boost=10,
        )
        # word search on the title
        query |= Q(
            "simple_query_string",
            query=f"{title}",
            fields=["title._text"],
            default_operator="AND",
            flags="WHITESPACE",
            boost=5,
        )
        # title AND provisionActivity AND 1th author should match the complete record
        query |= Q(
            "simple_query_string",
            query=f"{data_text}",
            default_operator="AND",
            flags="WHITESPACE",
            boost=2,
        )
        # title OR provisionActivity OR 1th author should match the complete record
        query |= Q(
            "simple_query_string",
            query=f"{data_text}",
            flags="WHITESPACE",
            default_operator="OR",
        )
        search = self.search.query(query)

        # add score
        candidates = [
            (hit._source.pid, hit._source.to_dict()) + self.rescore(data, hit)
            for hit in search.execute().hits.hits
        ]

        # sort by score
        candidates.sort(key=lambda val: val[2], reverse=True)
        return [c for c in candidates if c[2] > 0.6]

    def get_candidates(self, data):
        """Get similar existing documents."""
        if not data:
            return []

        # add identifier alternatives
        IndexerDumper._process_identifiers({}, data)
        if identifier_candidates := self.get_identifiers_candidates(data):
            return identifier_candidates

        # ------ no match thus use text queries ----------
        # compute the sort_title value
        IndexerDumper._process_sort_title({}, data)
        # compute the provision activity text value
        IndexerDumper._process_provision_activity(data, data)
        ProvisionActivitiesExtension().post_dump({}, data)
        return self.get_text_candidates(data)
