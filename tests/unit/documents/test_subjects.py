# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Tests subject classes for documents."""
import mock
import pytest
from utils import mock_response

from rero_ils.modules.contributions.api import Contribution
from rero_ils.modules.documents.commons import SubjectFactory
from rero_ils.modules.documents.models import DocumentSubjectType
from rero_ils.modules.utils import get_ref_for_pid


def test_document_local_subjects():
    """Test local document subjects classes and factory."""

    # SUCCESS
    subjects = [{
        'data': {
            'conference': False,
            'place_subdivisions': ['New-York', 'United-States'],
            'preferred_name': 'ONU',
            'type': DocumentSubjectType.ORGANISATION
        },
        'result': 'ONU - New-York - United-States'
    }, {
        'data': {
            'temporal_subdivisions': ['(1922-1976)'],
            'place_subdivisions': ['Martigny', 'Suisse'],
            'preferred_name': 'Jean Dupont',
            'type': DocumentSubjectType.PERSON
        },
        'result': 'Jean Dupont - (1922-1976) - Martigny - Suisse'
    }, {
        'data': {
            'title': 'RERO for dummies',
            'creator': 'RERO & UCLouvain teams',
            'type': DocumentSubjectType.WORK
        },
        'result': 'RERO for dummies / RERO & UCLouvain teams'
    }, {
        'data': {
            'term': 'horlogerie',
            'type': DocumentSubjectType.TOPIC
        },
        'result': 'horlogerie'
    }]
    for subject in subjects:
        s = SubjectFactory.create_subject(subject['data'])
        assert s.render() == subject['result']

    # ERRORS
    data = {
        'preferred_name': 'Error',
        'type': DocumentSubjectType.TOPIC
    }
    with pytest.raises(AttributeError) as error:
        SubjectFactory.create_subject(data).render()
    assert 'term' in str(error.value)
    data = {
        'term': 'Error',
        'type': DocumentSubjectType.WORK
    }
    with pytest.raises(AttributeError) as error:
        SubjectFactory.create_subject(data).render()
    assert 'title' in str(error.value)
    data = {
        'term': 'Error',
        'type': DocumentSubjectType.ORGANISATION
    }
    with pytest.raises(AttributeError) as error:
        SubjectFactory.create_subject(data).render()
    assert 'preferred_name' in str(error.value)
    data = {
        'term': 'Error',
        'type': 'dummy'
    }
    with pytest.raises(AttributeError):
        SubjectFactory.create_subject(data).render()
    data = {
        'term': 'No type'
    }
    with pytest.raises(AttributeError):
        SubjectFactory.create_subject(data).render()


@mock.patch('requests.get')
def test_document_referenced_subject(mock_contributions_mef_get,
                                     mef_agents_url,
                                     contribution_person_response_data,
                                     contribution_person):
    """Test referenced document subjects."""
    mock_contributions_mef_get.return_value = mock_response(
        json_data=contribution_person_response_data)

    # REFERENCED SUBJECTS - SUCCESS
    data = {
        '$ref': f'{mef_agents_url}/idref/223977268',
        'type': DocumentSubjectType.PERSON
    }
    subject = SubjectFactory.create_subject(data)
    assert subject.render(language='ger') == 'Loy, Georg, 1885-19..'
    assert subject.render(language='dummy') == 'Loy, Georg, 1885-19..'
    assert subject.render() == 'Loy, Georg, 1885-19..'

    # REFERENCED SUBJECTS - ERRORS
    data = {
        '$dummy_ref': get_ref_for_pid(Contribution, contribution_person.pid),
        'type': DocumentSubjectType.PERSON
    }
    with pytest.raises(AttributeError):
        SubjectFactory.create_subject(data).render()
