# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test the escaping of the terms the editor sends to MEF."""

import pytest

from rero_ils.modules.entities.remote_entities.proxy import MEFProxyMixin, escape_query_term, quote_query_term


@pytest.mark.parametrize(
    ("term", "escaped"),
    [
        ("Bern : Kanton", r"Bern \: Kanton"),
        ("Paul / Peter", r"Paul \/ Peter"),
        ("Paris > Lyon < Genève", "Paris > Lyon < Genève"),
        ("Mozart!", r"Mozart\!"),
        ("Wien {Stadt}", r"Wien \{Stadt\}"),
        ("Assistance technique [+ adjectif]", r"Assistance technique \[\+ adjectif\]"),
        ("Rousseau ^", r"Rousseau \^"),
        ("AND", "and"),
        ("Jean OR Paul NOT Pierre", "Jean or Paul not Pierre"),
        ("Goethe", "Goethe"),
        ("Andorra Orléans Notre-Dame", r"Andorra Orléans Notre\-Dame"),
        ("O'Brien", "O'Brien"),
        (r"a\b", r"a\\b"),
    ],
)
def test_escape_query_term(term, escaped):
    """An unquoted term carries no query syntax."""
    assert escape_query_term(term) == escaped


def test_quote_query_term():
    """A quoted term only needs its own quotes and backslashes escaped."""
    assert quote_query_term('Ecole "libre"') == r"Ecole \"libre\""
    assert quote_query_term(r"a\b") == r"a\\b"
    assert quote_query_term("Bern : Kanton") == "Bern : Kanton"


def test_query_keeps_every_word_on_the_field():
    """Every word of a multi-word term is searched in `autocomplete_name`, not only the first one."""
    proxy = MEFProxyMixin.__new__(MEFProxyMixin)
    proxy.sources, proxy.filters = [], []
    assert "autocomplete_name:(Jean Paul Sartre)" in proxy._get_query_params("Jean Paul Sartre")[0]
