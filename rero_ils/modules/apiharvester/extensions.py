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

"""Api harvest extensions."""


import click

from ..contributions.api import Contribution, ContributionsSearch


class ApiHarvesterExtensionAgentMef():
    """API harvester extension.

    Handels record extraction and processing.
    """

    name = 'agent_mef'

    def process_records(self, api_harvester, records, verbose):
        """Process records.

        :param api_harvester: Api harvester instance.
        :param records: records to process.
        """
        if self.name == api_harvester.name:
            count = 0
            pids = []
            found_records = {}
            # find all existing pids in ES.
            for record in records:
                pid = record.get('pid')
                pids.append(pid)
                found_records[pid] = record
            query = ContributionsSearch().filter('terms', pid=pids)
            es_pids = [hit.pid for hit in query.source('pid').scan()]
            for pid in es_pids:
                cont = Contribution.get_record_by_pid(pid)
                record = found_records[pid]
                record['$schema'] = cont['$schema']
                # TODO: see if we can use the MD5
                if record != cont:
                    count += 1
                    # update the contribution
                    cont.replace(data=record, dbcommit=True, reindex=True)
                    # reindex the documents
                    doc_count = cont.reindex_documents()
                    if verbose:
                        click.echo(f'  Update contribution: {cont.pid}'
                                   f' documents: {doc_count}')

        return count, records
