# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Common acquisition dumpers."""

from invenio_records.dumpers import Dumper

from rero_ils.modules.commons.dumpers import MultiDumper
from rero_ils.modules.commons.identifiers import IdentifierType, \
    QualifierIdentifierRenderer
from rero_ils.modules.documents.dumpers import TitleDumper
from rero_ils.modules.documents.extensions import \
    ProvisionActivitiesExtension, SeriesStatementExtension


class DocumentAcquisitionDumper(Dumper):
    """Document dumper class for acquisition resources."""

    def dump(self, record, data):
        """Dump a document instance for acquisition.

        :param record: The record to dump.
        :param data: The initial dump data passed in by ``record.dumps()``.
        """
        # provision activity ------------------------
        provision_activities = filter(None, [
            ProvisionActivitiesExtension.format_text(activity)
            for activity in record.get('provisionActivity', [])
        ])
        provision_activity = next(iter(provision_activities or []), None)
        if provision_activity:
            provision_activity = provision_activity[0]['value']

        # series statement --------------------------
        series_statements = filter(None, [
            SeriesStatementExtension.format_text(statement)
            for statement in record.get('seriesStatement', [])
        ])
        series_statement = next(iter(series_statements or []), None)
        if series_statement:
            series_statement = series_statement[0]['value']

        # identifiers -------------------------------
        identifiers = record.get_identifiers(
            filters=[IdentifierType.ISBN, IdentifierType.EAN],
            with_alternatives=True
        )
        # keep only EAN identifiers - only EAN identifiers should be included
        # into acquisition notification.
        render_class = QualifierIdentifierRenderer()
        identifiers = [
            identifier.render(render_class=render_class)
            for identifier in identifiers
            if identifier.type == IdentifierType.EAN
        ]

        data.update({
            'identifiers': identifiers,
            'provision_activity': provision_activity,
            'serie_statement': series_statement
        })
        data = {k: v for k, v in data.items() if v}
        return data


# specific acquisition dumper
document_acquisition_dumper = MultiDumper(dumpers=[
    # make a fresh copy
    Dumper(),
    TitleDumper(),
    DocumentAcquisitionDumper()
])
