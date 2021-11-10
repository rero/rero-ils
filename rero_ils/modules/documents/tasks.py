# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Celery tasks to documents."""

from __future__ import absolute_import, print_function

import click
from celery import shared_task
# from celery.task.control import inspect
from flask import current_app

from .api import Document, DocumentsSearch
from ..contributions.api import Contribution


@shared_task(ignore_result=True)
def find_contribution(verbose=False):
    """Records creation and indexing.

    :param verbose: Verbose print.
    :returns: cont_found cunt, cont_exists count,
              IdRef not cont_found count, MEF not cont_found count
    """
    query = DocumentsSearch() \
        .filter('exists', field='contribution.agent.identifiedBy') \
        .source(['pid']) \
        .scan()
    cont_found = {}
    cont_exists = {}
    cont_no_idref = {}
    cont_no_mef = {}
    mef_url = current_app.config.get('RERO_ILS_MEF_AGENTS_URL')
    for hit in query:
        doc = Document.get_record_by_id(hit.meta.id)
        new_contributions = []
        changed = False
        for contribution in doc.get('contribution', []):
            cont = None
            new_contributions.append(contribution)
            ref_type = contribution['agent'].get(
                'identifiedBy', {}).get('type', '').lower()
            ref_pid = contribution['agent'].get(
                'identifiedBy', {}).get('value')
            ref = f'{ref_type}/{ref_pid}'
            if ref_type and ref_pid:
                # Try to get existing contribution
                cont = Contribution.get_contribution(ref_type, ref_pid)
                if not cont:
                    # contribution does not exist
                    try:
                        # try to get the contribution online
                        data = Contribution._get_mef_data_by_type(
                            ref_pid, ref_type)
                        metadata = data['metadata']
                        if metadata.get('idref'):
                            cont_found.setdefault(
                                ref,
                                {'count': 0, 'mef': metadata.get('pid')}
                            )
                            cont_found[ref]['count'] += 1
                            # create local contribution
                            metadata.pop('$schema', None)
                            cont = Contribution.create(
                                data=metadata, dbcommit=True, reindex=True)
                        else:
                            # online contribution has no IdREf
                            cont_no_idref.setdefault(ref, 0)
                            cont_no_idref[ref] += 1
                    except Exception:
                        # no online contribution found
                        cont_no_mef.setdefault(ref, 0)
                        cont_no_mef[ref] += 1
                else:
                    # contribution exist allready
                    cont_exists.setdefault(ref, 0)
                    cont_exists[ref] += 1
            if cont:
                # change the contribution to linked contribution
                if cont.get('idref'):
                    changed = True
                    url = f'{mef_url}/idref/{cont["idref"]["pid"]}'
                    new_contributions[-1]['agent'] = {
                        '$ref': url,
                        'type': contribution['agent']['type']
                    }
                else:
                    # contribution has no IdREf
                    cont_no_idref.setdefault(ref, 0)
                    cont_no_idref[ref] += 1
        if changed:
            doc['contribution'] = new_contributions
            doc.update(data=doc, dbcommit=True, reindex=True)
    if verbose:
        if cont_found:
            click.secho('Found:', fg='green')
            for key, value in cont_found.items():
                click.echo(f'\t{key}  MEF pid: {value["mef"]} '
                           f'count: {value["count"]}')
        for msg, data in {
            'Exist:': cont_exists,
            'No IdRef:': cont_no_idref,
            'No Mef:': cont_no_mef
        }.items():
            if data:
                click.secho(msg, fg='yellow')
                for key, value in data.items():
                    click.echo(f'\t{key}  count: {value}')
    return (
        len(cont_found),
        len(cont_exists),
        len(cont_no_idref),
        len(cont_no_mef)
    )
