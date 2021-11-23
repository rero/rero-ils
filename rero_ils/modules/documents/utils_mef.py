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

from abc import ABC, abstractmethod

import click
from elasticsearch_dsl import Q
from flask import current_app

from .api import Document, DocumentsSearch
from ..contributions.api import Contribution
from ..utils import set_timestamp


class ReplaceMefIdentifiedBy(ABC):
    """Replace MEF identified by base class."""

    def __init__(self, mef_url, run=False, verbose=False):
        """Constructor."""
        self.mef_url = mef_url
        self.count_found = {}
        self.count_exists = {}
        self.count_no_data = {}
        self.count_no_mef = {}
        self.verbose = verbose
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

    def increment_count(self, count, ref):
        """Increment count.

        :param count: count to use.
        :param ref: reference to increment.
        """
        count.setdefault(ref, 0)
        count[ref] += 1

    @property
    def counts(self):
        """Counts."""
        return (self.count_found, self.count_exists, self.count_no_data,
                self.count_no_mef)

    @property
    def counts_len(self):
        """Counts."""
        return (len(self.count_found), len(self.count_exists),
                len(self.count_no_data), len(self.count_no_mef))

    def print_counts(self):
        """Print counts."""
        click.echo(
            f'Found  : {len(self.count_found)} '
            f'Exists : {len(self.count_exists)} '
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
        if self.count_no_data:
            click.echo('No Data:')
            for key in sorted(self.count_no_data.keys()):
                click.echo(f'  {key:<20} : {self.count_no_data[key]}')
        if self.count_no_mef:
            click.echo('No MEF:')
            for key in sorted(self.count_no_mef.keys()):
                click.echo(f'  {key:<20} : {self.count_no_mef[key]}')

    def set_timestamp(self):
        """Set timestamp."""
        counts = self.counts
        counts = {
            'found': counts[0],
            'exists': counts[1],
            'no_data': counts[2],
            'no_mef': counts[3]
        }
        set_timestamp(self.__class__.__name__, **counts)


class ReplaceMefIdentifiedByContribution(ReplaceMefIdentifiedBy):
    """Replace MEF identified by contribution class."""

    def __init__(self, run=False, verbose=False):
        """Constructor."""
        mef_url = current_app.config.get('RERO_ILS_MEF_AGENTS_URL')
        super().__init__(run=run, mef_url=mef_url, verbose=verbose)
        self.cont_types = ['idref', 'gnd']

    def _query_filter(self):
        """Query filter to find documents."""
        return DocumentsSearch() \
            .filter('exists', field='contribution.agent.identifiedBy')

    def get_local(self, ref_type, ref_pid):
        """Get local MEF record."""
        return Contribution.get_contribution(ref_type, ref_pid)

    def get_online(self, ref_type, ref_pid):
        """Get online MEF record."""
        ref = f'{ref_type}/{ref_pid}'
        try:
            # try to get the contribution online
            data = Contribution._get_mef_data_by_type(ref_pid, ref_type)
            metadata = data['metadata']
            if metadata.get('idref') or metadata.get('gnd'):
                self.increment_count(self.count_found, ref)
                # delete mef $schema
                metadata.pop('$schema', None)
                # create local contribution
                return Contribution.create(data=metadata, dbcommit=True,
                                           reindex=True)
            else:
                # online contribution has no IdREf, GND or RERO
                self.increment_count(self.count_no_data, ref)
        except Exception as err:
            # no online contribution found
            self.increment_count(self.count_no_mef, ref)

    def process(self):
        """Process replacement."""
        if self.verbose:
            click.echo(f'Found: {self._query_filter().count()}')
        for hit in self._query_filter().source('pid').scan():
            doc = Document.get_record_by_id(hit.meta.id)
            new_contributions = []
            changed = False
            for contribution in doc.get('contribution', []):
                new_contributions.append(contribution)
                ref_type = contribution['agent'].get(
                    'identifiedBy', {}).get('type', '').lower()
                if ref_type in self.cont_types + ['rero']:
                    ref_pid = contribution['agent'].get(
                        'identifiedBy', {}).get('value')
                    cont = self.get_local(ref_type=ref_type, ref_pid=ref_pid)
                    if not cont:
                        cont = self.get_online(ref_type=ref_type,
                                               ref_pid=ref_pid)
                    if cont:
                        # change the contribution to linked contribution
                        for cont_type in self.cont_types:
                            if cont.get('cont_type'):
                                changed = True
                                url = f'{self.mef_url}/{cont_type}/' \
                                    f'{cont[cont_type]["pid"]}'
                                new_contributions[-1]['agent'] = {
                                    '$ref': url,
                                    'type': contribution['agent']['type']
                                }
                                break
            if changed:
                doc['contribution'] = new_contributions
                doc.update(data=doc, dbcommit=True, reindex=True)
                if self.verbose:
                    click.echo(f'  Changed document: {doc.pid}')
        return self.counts


class ReplaceMefIdentifiedBySubjects(ReplaceMefIdentifiedByContribution):
    """Replace MEF identified by subjects class."""

    def _query_filter(self):
        """Query filter to find documents."""
        return DocumentsSearch() \
            .filter('exists', field='subjects.identifiedBy') \
            .filter('bool', should=[
                Q('term', subjects__type='bf:Person'),
                Q('term', subjects__type='bf:Organisation')
            ])

    def process(self):
        """Process replacement."""
        if self.verbose:
            click.echo(f'Found: {self._query_filter().count()}')
        for hit in self._query_filter().source('pid').scan():
            doc = Document.get_record_by_id(hit.meta.id)
            new_subjects = []
            changed = False
            for subject in doc.get('subjects', []):
                new_subjects.append(subject)
                ref_type = subject.get(
                    'identifiedBy', {}).get('type', '').lower()
                if ref_type in self.cont_types + ['rero']:
                    ref_pid = subject.get('identifiedBy', {}).get('value')
                    cont = self.get_local(ref_type=ref_type, ref_pid=ref_pid)
                    if not cont:
                        cont = self.get_online(ref_type=ref_type,
                                               ref_pid=ref_pid)
                    if cont:
                        # change the contribution to linked contribution
                        for cont_type in ['idref', 'gnd']:
                            if cont.get('cont_type'):
                                changed = True
                                url = f'{self.mef_url}/{cont_type}/' \
                                    f'{cont[cont_type]["pid"]}'
                                new_subjects[-1]['agent'] = {
                                    '$ref': url,
                                    'type': subject['type']
                                }
                                break
            if changed:
                doc['subjects'] = new_subjects
                doc.update(data=doc, dbcommit=True, reindex=True)
        return self.counts
