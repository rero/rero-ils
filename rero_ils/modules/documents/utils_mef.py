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

import contextlib
from abc import ABC, abstractmethod

import click
from elasticsearch_dsl import Q
from flask import current_app
from sqlalchemy.orm.exc import NoResultFound
from webargs import ValidationError

from .api import Document, DocumentsSearch
from ..contributions.api import Contribution
from ..utils import set_timestamp


class ReplaceMefIdentifiedBy(ABC):
    """Replace MEF identified by base class."""

    name = ''

    def __init__(self, mef_url, run=False, verbose=False, debug=False):
        """Constructor."""
        self.mef_url = mef_url
        self.count_found = {}
        self.count_exists = {}
        self.count_deleted = {}
        self.count_no_data = {}
        self.count_no_mef = {}
        self.preferred_names = {}
        self.verbose = verbose
        self.debug = debug
        if run:
            self.process()

    @abstractmethod
    def _query_filter(self):
        """Query filter to find documents."""
        raise NotImplementedError()

    @abstractmethod
    def get_local(self):
        """Get local MEF record."""
        raise NotImplementedError()

    @abstractmethod
    def get_online(self):
        """Get online MEF record."""
        raise NotImplementedError()

    @abstractmethod
    def process(self):
        """Process replacement."""
        raise NotImplementedError()

    def increment_count(self, count, ref, msg):
        """Increment count.

        :param count: count to use.
        :param ref: reference to increment.
        """
        self.print_debug(f'{msg}: {ref}')
        count.setdefault(ref, 0)
        count[ref] += 1

    def add_preferred_name(self, ref_type, ref_pid, preferred_name, type):
        """Add preferred name."""
        ref = f'{ref_type}/{ref_pid}'
        self.preferred_names[ref] = {
            'type': f'{type:<15}',
            'preferred_name': f'"{preferred_name}"'
        }

    @property
    def counts(self):
        """Counts."""
        return (self.count_found, self.count_exists, self.count_deleted,
                self.count_no_data, self.count_no_mef)

    @property
    def counts_len(self):
        """Counts."""
        return (len(self.count_found), len(self.count_exists),
                len(self.count_deleted), len(self.count_no_data),
                len(self.count_no_mef))

    def print_counts(self):
        """Print counts."""
        click.echo(
            f'Found  : {len(self.count_found)} '
            f'Exists : {len(self.count_exists)} '
            f'Deleted: {len(self.count_deleted)} '
            f'No Data: {len(self.count_no_data)} '
            f'No MEF : {len(self.count_no_mef)}'
        )

    def print_details(self):
        """Print details count."""
        if self.count_found:
            click.echo('Found:')
            for key in sorted(self.count_found.keys()):
                click.echo(f'  {key:<20} : {self.count_found[key]}')
        if self.count_exists:
            click.echo('Exists:')
            for key in sorted(self.count_exists.keys()):
                click.echo(f'  {key:<20} : {self.count_exists[key]}')
        if self.count_deleted:
            click.echo('Deleted:')
            for key in sorted(self.count_deleted.keys()):
                info = self.preferred_names.get(key, {}).values()
                click.echo(f'  {key:<20} : {self.count_deleted[key]:>4}'
                           f'\t{"    ".join(info)}')
        if self.count_no_data:
            click.echo('No Data:')
            for key in sorted(self.count_no_data.keys()):
                info = self.preferred_names.get(key, {}).values()
                click.echo(f'  {key:<20} : {self.count_no_data[key]:>4}'
                           f'\t{"    ".join(info)}')
        if self.count_no_mef:
            click.echo('No MEF:')
            for key in sorted(self.count_no_mef.keys()):
                info = self.preferred_names.get(key, {}).values()
                click.echo(f'  {key:<20}{self.count_no_mef[key]:>4}'
                           f'\t{"    ".join(info)}')

    def print_debug(self, *args, **kwargs):
        """Print debug messages."""
        if self.debug:
            for arg in args:
                click.secho(str(arg), fg='yellow')

    def set_timestamp(self):
        """Set timestamp."""
        counts = self.counts
        counts = {
            'found': counts[0],
            'exists': counts[1],
            'deleted': counts[2],
            'no_data': counts[3],
            'no_mef': counts[4]
        }
        set_timestamp(f'ReplaceMefIdentifiedBy_{self.name}', **counts)

    def update_document(self, changed, document):
        """Update document."""
        if changed:
            try:
                document.update(data=document, dbcommit=True, reindex=True)
            except ValidationError as err:
                click.secho(f'{document.pid} {err} {document}', fg='red')


class ReplaceMefIdentifiedByContribution(ReplaceMefIdentifiedBy):
    """Replace MEF identified by contribution class."""

    name = 'contribution'

    def __init__(self, run=False, verbose=False, debug=False):
        """Constructor."""
        mef_url = current_app.config.get('RERO_ILS_MEF_AGENTS_URL')
        super().__init__(
            run=run, mef_url=mef_url, verbose=verbose, debug=debug)
        self.cont_types = ['idref', 'gnd']

    def _query_filter(self):
        """Query filter to find documents."""
        return DocumentsSearch() \
            .filter('exists', field='contribution.agent.identifiedBy')

    def get_local(self, ref_type, ref_pid):
        """Get local MEF record."""
        return Contribution.get_contribution(ref_type, ref_pid)

    def get_online(self, doc_pid, ref_type, ref_pid):
        """Get online MEF record."""
        ref = f'{ref_type}/{ref_pid}'
        try:
            # try to get the contribution online
            data = Contribution._get_mef_data_by_type(ref_pid, ref_type)
            if data.get('idref') or data.get('gnd'):
                if data.get('deleted'):
                    self.increment_count(self.count_deleted, ref,
                                         f'{doc_pid} Deleted')
                else:
                    self.increment_count(self.count_found, ref,
                                         f'{doc_pid} Online found')
                    # create and return local contribution
                    return Contribution.create(data=data, dbcommit=True,
                                               reindex=True)
            else:
                # online contribution has no IdREf, GND or RERO
                self.increment_count(self.count_no_data, ref,
                                     f'{doc_pid} Online no data')
        except Exception as err:
            # no online contribution found
            self.increment_count(self.count_no_mef, ref,
                                 f'{doc_pid:>10}\tNo online MEF')

    def get_contribution(self, doc_pid, ref_type, ref_pid):
        """Get Contribution."""
        if contribution := self.get_local(ref_type=ref_type, ref_pid=ref_pid):
            self.increment_count(self.count_exists, f'{ref_type}/{ref_pid}',
                                 f'{doc_pid} Exists')
            return contribution
        return self.get_online(doc_pid=doc_pid, ref_type=ref_type,
                               ref_pid=ref_pid)

    def process(self):
        """Process replacement."""
        if self.verbose:
            click.echo(f'Found identifiedBy contributions: '
                       f'{self._query_filter().count()}')
        for hit in list(self._query_filter().source('pid').scan()):
            with contextlib.suppress(NoResultFound):
                doc = Document.get_record_by_id(hit.meta.id)
                changed = False
                for contribution in doc.get('contribution', []):
                    ref_type = contribution['agent'].get(
                        'identifiedBy', {}).get('type', '').lower()
                    if ref_type in self.cont_types + ['rero']:
                        ref_pid = contribution['agent'].get(
                            'identifiedBy', {}).get('value')
                        if cont := self.get_contribution(hit.pid, ref_type,
                                                         ref_pid):
                            # change the contribution to linked contribution
                            for cont_type in self.cont_types:
                                if cont.get(cont_type):
                                    changed = True
                                    url = f'{self.mef_url}/{cont_type}/' \
                                        f'{cont[cont_type]["pid"]}'
                                    new_contribution = {
                                        '$ref': url,
                                        'type': contribution['agent']['type']
                                    }
                                    self.print_debug(
                                        f'{hit.pid} Change:',
                                        f'  {contribution["agent"]}',
                                        f'  {new_contribution}'
                                    )
                                    contribution['agent'] = new_contribution
                                    break
                        else:
                            self.add_preferred_name(
                                ref_type=ref_type,
                                ref_pid=ref_pid,
                                preferred_name=contribution.get(
                                    'agent', {}).get('preferred_name', ''),
                                type=contribution.get(
                                    'agent', {}).get('type', ''),
                            )
                self.update_document(changed=changed, document=doc)
        return self.counts


class ReplaceMefIdentifiedBySubjects(ReplaceMefIdentifiedByContribution):
    """Replace MEF identified by subjects class."""

    def __init__(self, run=False, verbose=False, debug=False,
                 subjects='subjects'):
        """Constructor."""
        super().__init__(run=run, verbose=verbose, debug=debug)
        assert subjects in ['subjects', 'subjects_imported']
        self.name = subjects

    def _query_filter(self):
        """Query filter to find documents."""
        return DocumentsSearch() \
            .filter('bool', must=[
                Q('exists', field=f'{self.name}.identifiedBy'),
                Q({'terms': {
                    f'{self.name}.type': ['bf:Person', 'bf:Organisation']
                }})
            ])

    def process(self):
        """Process replacement."""
        if self.verbose:
            click.echo(f'Found identifiedBy {self.name}: '
                       f'{self._query_filter().count()}')
        hits = list(self._query_filter().source('pid').scan())
        for hit in list(self._query_filter().source('pid').scan()):
            with contextlib.suppress(NoResultFound):
                doc = Document.get_record_by_id(hit.meta.id)
                changed = False
                for subject in doc.get(self.name, []):
                    ref_type = subject.get(
                        'identifiedBy', {}).get('type', '').lower()
                    is_pers_org = subject.get('type') in [
                        'bf:Person', 'bf:Organisation']
                    if ref_type in self.cont_types + ['rero'] and is_pers_org:
                        ref_pid = subject.get('identifiedBy', {}).get('value')
                        if cont := self.get_contribution(hit.pid, ref_type,
                                                         ref_pid):
                            # change the contribution to linked contribution
                            for cont_type in ['idref', 'gnd']:
                                if cont.get(cont_type):
                                    changed = True
                                    url = f'{self.mef_url}/{cont_type}/' \
                                        f'{cont[cont_type]["pid"]}'
                                    new_subject = {
                                        '$ref': url,
                                        # TOTO: we have to correct all wrong
                                        # bf:Organisation
                                        'type': subject['type']
                                    }
                                    self.print_debug(
                                        f'{hit.pid} Change:',
                                        f'  {subject}',
                                        f'  {new_subject}'
                                    )
                                    subject = new_subject
                                    break
                        else:
                            self.add_preferred_name(
                                ref_type=ref_type,
                                ref_pid=ref_pid,
                                preferred_name=subject.get('preferred_name'),
                                type=subject.get('type')
                            )
                self.update_document(changed=changed, document=doc)
        return self.counts
