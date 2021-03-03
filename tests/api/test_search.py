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

"""Search tests."""

from flask import url_for
from utils import get_json, login_user_via_session


def test_document_search(
        client,
        doc_title_travailleurs,
        doc_title_travailleuses
):
    """Test document search queries."""
    # phrase search
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='"Les travailleurs assidus sont de retours"',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # phrase search with punctuations
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='"Les travailleurs assidus sont de retours."',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # word search
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='travailleurs',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 2

    # travailleurs == travailleur == travailleuses
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='travailleur',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 2

    # ecole == école
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='ecole',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # Ecole == école
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='Ecole',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # ECOLE == école
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='Ecole',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # _école_ == école
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q=' école ',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # Müller
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='Müller',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # Müller == Muller
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='Muller',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # Müller == Mueller
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='Mueller',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # test AND
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='travailleuse école',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # test OR in two docs
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='retours | école',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 2

    # test AND in two fields (travailleuses == travailleur)
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='travailleuses bientôt',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='travailleuses +bientôt',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # test NOT
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='travailleur -école',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # test OR in two docs (each match only one term)
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='retours | école',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 2

    # test AND in two docs (each match only one term) => no result
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='retours école',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 0

    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='retours + école',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 0

    # title + subtitle
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='Les travailleurs assidus sont de retours : '
          'les jeunes arrivent bientôt ?',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # punctuation
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q=r'école : . ... , ; ? \ ! = == - --',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    list_url = url_for(
        'invenio_records_rest.doc_list',
        q=r'école:.,;?\!...=-==--',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # special chars
    # œ in title
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q=r'bœuf',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # æ in title
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q=r'ex aequo',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # æ in title
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q=r'ÆQUO',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # œ in author
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q=r'Corminbœuf',
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1


def test_patrons_search(
        client,
        librarian_martigny
):
    """Test document boosting."""
    login_user_via_session(client, librarian_martigny.user)
    birthdate = librarian_martigny.dumps()['birth_date']
    # complete birthdate
    list_url = url_for(
        'invenio_records_rest.ptrn_list',
        q='{birthdate}'.format(birthdate=birthdate),
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1

    # birth year
    list_url = url_for(
        'invenio_records_rest.ptrn_list',
        q='{birthdate}'.format(birthdate=birthdate.split('-')[0]),
        simple='1'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total']['value'] == 1
