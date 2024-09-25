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

"""Mock Modules."""

from dojson.contrib.marc21.utils import create_record
from lxml import etree

from rero_ils.modules.deduplications.api import Deduplication
from rero_ils.modules.documents.dojson.contrib.marc21tojson.rero import marc21
from rero_ils.modules.imports.serializers.serializers import ImportsMarcSearchSerializer
from rero_ils.modules.utils import read_xml_record


class Marc21XMLConverter:
    """Marc21XML converter class."""

    @classmethod
    def convert(cls, data):
        """Convert a xml marc 21 data into a RERO ILS JSON format."""
        converted = marc21.do(create_record(data))
        _id = None
        for identifier in converted.get("identifiedBy", []):
            if identifier.get("source") == "RERO":
                _id = identifier["value"]
        if _id is None:
            logs = dict(
                warning=["Fixtures conversions"],
                error=["Unable to extract the main identifier"],
            )
            return None, {}, "error", logs
        logs = dict(
            info=["Conversion ok"],
            warning=["Fixtures conversions"],
        )
        return _id, converted, "complete", logs

    @classmethod
    def loads(cls, file):
        """Read a marc xml file and iterate over all records."""
        for record in read_xml_record(file):
            yield etree.tostring(
                record, encoding="utf-8", method="xml", pretty_print=True
            )

    @classmethod
    def markdown(cls, data):
        """Convert an marc21 xml record into a markdown table."""
        record = ImportsMarcSearchSerializer.convert_marc_to_marc_text_dict(
            create_record(data)
        )
        formatted_record = ["| Marc&nbsp;Field | Marc&nbsp;Value |", "| --- | --- |"]
        for leader, fields in record:
            leader = leader.replace(" ", "&nbsp;")
            if isinstance(fields, list):
                subfields = []
                for field in fields:
                    field[0] = f"${field[0]}"
                    subfields.append(" ".join(field))
                fields = " ".join(subfields)
            formatted_record.append(f"| {leader} | {fields} |")
        return "\n".join(formatted_record)

    @classmethod
    def dedup(cls, data, force=False):
        """Deduplication function.

        :param data: Data of record.
        :param force: Force recalculation of score if exists.
        :returns: ils_pid,logs, status and candidates.
        """
        ils_pid = None
        if data.conversion.status == "error":
            return (
                ils_pid,
                {
                    "warning": [
                        "Merci de résoudre les erreurs de conversion avant de dédoublonner."
                    ]
                },
                "pending",
                [],
            )
        candidates = [
            (c.pid, c.json.to_dict(), c.score, c.detailed_score.to_dict())
            for c in data.deduplication.candidates
        ]
        logs = {}
        status = "no match"
        if data.deduplication.status == "pending" or force:
            try:
                candidates = Deduplication().get_candidates(
                    data.conversion.json.to_dict()
                )
            except Exception as err:
                logs["error"] = [f"{err}"]
                status = "error"
        if status != "error":
            if not candidates:
                status = "no match"
            else:
                scores = [c[2] for c in candidates]
                if max(scores) < 0.8:
                    status = "check"
                elif len([s for s in scores if s > 0.8]) > 1:
                    status = "multiple match"
                else:
                    status = "match"
                    best = candidates[0]
                    best_detailed_score = best[-1]
                    # force check status if the publication date mismatch
                    if (
                        best_detailed_score.get("publication_date")
                        and best_detailed_score["publication_date"]["value"] < 1
                    ):
                        status = "check"
                        logs["warning"] = [
                            "Date de publication inexacte: le statut 'check' a été forcé."
                        ]
                    ils_pid = best[0]
        return ils_pid, logs, status, candidates
