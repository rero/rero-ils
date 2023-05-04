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

"""Test CQL parser."""

import pytest

from rero_ils.modules.sru.cql_parser import RESERVED_PREFIXES, Boolean, \
    Diagnostic, Index, ModifiableObject, ModifierClause, PrefixableObject, \
    PrefixedObject, Relation, SearchClause, Term, Triple, parse


def test_diagnostic():
    """Test Diagnostic class."""
    diag = Diagnostic()
    diag.code = 45
    diag.details = 'test'
    assert str(diag) == 'info:srw/diagnostic/1/45 [Malformed Query]: test'


def test_get_query_clause(app):
    """Check that simple clause is parsed correctly."""
    query = parse('dc.anywhere all "spam hamm"')
    # Check query instance
    assert isinstance(query, SearchClause)
    # Check Index
    assert isinstance(query.index, Index)
    assert query.index.prefix == 'dc'
    assert query.index.value == 'anywhere'
    # Check Relation
    assert isinstance(query.relation, Relation)
    assert query.relation.value == 'all'
    # Check Value
    assert isinstance(query.term, Term)
    assert query.term.value == '"spam hamm"'
    es_string = query.to_es()
    assert es_string == '(spam AND hamm)'

    query = parse('((title=spam) or (subtitle=hamm)) or eggs')
    es_string = query.to_es()
    assert es_string == '((title:spam OR subtitle:hamm) OR eggs)'
    assert query.get_result_set_id() == ''


def test_get_query_clause_no_xml_character(app):
    """Check that simple clause with non XML charactersis parsed correctly.

    All strings must be XML compatible: Unicode or ASCII,
    no NULL bytes or control characters
    """
    query = parse('dc.anywhere all ">>\x00<<"')
    # Check query instance
    assert isinstance(query, SearchClause)
    assert query.term.value == '">><<"'
    es_string = query.to_es()
    assert es_string == '(>><<)'


def test_get_query_clause_utf8(app):
    """Check that simple clause with utf8 is parsed correctly."""
    query = parse('dc.anywhere any "späm h\xe4mm"')
    # Check query instance
    assert isinstance(query, SearchClause)
    # Check Index
    assert isinstance(query.index, Index)
    assert query.index.prefix == 'dc'
    assert query.index.value == 'anywhere'
    # Check Relation
    assert isinstance(query.relation, Relation)
    assert query.relation.value == 'any'
    # Check Value
    assert isinstance(query.term, Term)
    assert query.term.value == '"späm hämm"'
    es_string = query.to_es()
    assert es_string == '(späm OR hämm)'


def test_get_query_clause_modifiers():
    """Check that relation modifiers are parsed correctly."""
    query = parse('dc.anywhere all/cql.stem/rel.algorithm=okapi "spam"')
    assert len(query.relation.modifiers) > 0
    for mod in query.relation.modifiers:
        assert isinstance(mod, ModifierClause)
    assert str(query.relation.modifiers[0].type) == 'cql.stem'
    assert str(query.relation.modifiers[1].type) == 'rel.algorithm'
    assert str(query.relation.modifiers[1].comparison) == '='
    assert str(query.relation.modifiers[1].value) == 'okapi'
    with pytest.raises(Diagnostic):
        query.to_es()


def test_get_query_clause_with_prefix(app):
    """Check that simple clause with prefix is parsed correctly."""
    query = parse(
        '>cql="info:srw/cql-context-set/1/cql-v1.1" cql.anywhere '
        'cql.all "spam"'
    )
    # Check query instance
    assert isinstance(query, SearchClause)
    # Check Index
    assert isinstance(query.index, Index)
    assert query.index.prefix == 'cql'
    assert query.index.value == 'anywhere'
    # Check Relation
    assert isinstance(query.relation, Relation)
    assert query.relation.value == 'all'
    # Check Value
    assert isinstance(query.term, Term)
    assert query.term.value == '"spam"'
    es_string = query.to_es()
    assert es_string == '(spam)'


def test_get_query_clause_with_relation_modifier():
    """Check that simple clause with relation modifier is parsed correctly."""
    query = parse(
        'anywhere all/relevant "spam"'
    )
    # Check query instance
    assert isinstance(query, SearchClause)
    # Check Index
    assert isinstance(query.index, Index)
    assert query.index.value == 'anywhere'
    # Check Relation
    assert isinstance(query.relation, Relation)
    assert query.relation.value == 'all'
    # Check Value
    assert isinstance(query.term, Term)
    assert query.term.value == '"spam"'
    with pytest.raises(Diagnostic) as err:
        query.to_es()
    assert str(err.value).startswith(
        'info:srw/diagnostic/1/21 '
        '[Unsupported combination of relation modifers]'
    )


def test_get_query_clause_with_sorting(app):
    """Check that simple clause with sorting is parsed correctly."""
    query = parse('"cat" sortBy title')
    # Check query instance
    assert isinstance(query, SearchClause)
    # Check Index
    assert isinstance(query.index, Index)
    assert query.index.value == 'serverchoice'
    # Check Relation
    assert isinstance(query.relation, Relation)
    assert query.relation.value == '='
    # Check Value
    assert isinstance(query.term, Term)
    assert query.term.value == '"cat"'
    with pytest.raises(Diagnostic) as err:
        query.to_es()
    assert str(err.value) == \
        'info:srw/diagnostic/1/80 [Sort not supported]: '


def test_get_query_clause_with_relation(app):
    """Check that relation clause is parsed correctly."""
    query = parse('year > 1999')
    # Check query instance
    assert isinstance(query, SearchClause)
    # Check Relation
    assert isinstance(query.relation, Relation)
    assert query.relation.value == '>'
    # Check Value
    assert isinstance(query.term, Term)
    assert query.term.value == '1999'
    es_string = query.to_es()
    assert es_string == 'year:>1999'
    query = parse(
        'ind1 = 1 AND ind2 > 2 AND ind3 >= 3 AND ' +
        'ind4 < 4 AND ind5 <= 5 AND ind6 <> 6'
    )
    es_string = query.to_es()
    assert es_string == (
        '(((((ind1:1 AND ind2:>2) AND ind3:>=3) '
        'AND ind4:<4) AND ind5:<=5) AND ind6:-"6")'
    )


def test_get_query_triple(app):
    """Check that query with boolean is parsed correctly."""
    query = parse('dc.anywhere all spam and dc.anywhere all eggs')
    # Check query instance
    assert isinstance(query, Triple)
    # Check left clause
    assert isinstance(query.left_operand, SearchClause)
    # remember terms get quoted during parsing
    assert query.left_operand.to_es() == '(spam)'
    # Check boolean
    assert isinstance(query.boolean, Boolean)
    assert query.boolean.value == 'and'
    # Check right clause
    assert isinstance(query.right_operand, SearchClause)
    # Remember terms get quoted during parsing
    assert query.right_operand.to_es() == '(eggs)'
    es_string = query.to_es()
    assert es_string == '((spam) AND (eggs))'
    query = parse("dc.anywhere prox spam")
    with pytest.raises(Diagnostic) as err:
        query.to_es()
    assert str(err.value) == (
        'info:srw/diagnostic/1/37 [Unsupported boolean operator]: prox'
    )
    assert query.get_result_set_id() == ''


def test_get_query_triple_with_sort(app):
    """Check that query with boolean is parsed correctly."""
    query = parse(
        'dc.anywhere all spam and dc.anywhere all eggs sortBy subtitle'
    )
    # Check query instance
    assert isinstance(query, Triple)
    with pytest.raises(Diagnostic) as err:
        query.to_es()
    assert str(err.value) == 'info:srw/diagnostic/1/80 [Sort not supported]: '


def test_get_query_with_modifiers():
    """Check that query with modifiers is parsed correctly."""
    # Relation Modifiers
    q_string = 'dc.anywhere any/relevant spam'
    query = parse(q_string)
    assert len(query.relation.modifiers) > 0
    for mod in query.relation.modifiers:
        assert isinstance(mod, ModifierClause)
    assert str(query.relation.modifiers[0].type) == 'cql.relevant'
    assert not str(query.relation.modifiers[0].comparison)
    assert not str(query.relation.modifiers[0].value)
    with pytest.raises(Diagnostic):
        query.to_es()

    # Boolean modifiers
    q_string = 'dc.anywhere all spam and/rel.combine=sum dc.anywhere all eggs'
    query = parse(q_string)
    assert len(query.boolean.modifiers) > 0
    for mod in query.boolean.modifiers:
        assert isinstance(mod, ModifierClause)
    assert str(query.boolean.modifiers[0].type) == 'rel.combine'
    assert str(query.boolean.modifiers[0].comparison) == '='
    assert str(query.boolean.modifiers[0].value) == 'sum'
    with pytest.raises(Diagnostic):
        query.to_es()


def test_errors():
    """Check errors are trown correctly."""
    q_string = ''
    with pytest.raises(Diagnostic) as err:
        parse(q_string)
    assert str(err.value) == (
        'info:srw/diagnostic/1/10 [Malformed Query]: '
        'Expected Boolean or Relation but got: '
    )
    q_string = '123 456'
    with pytest.raises(Diagnostic) as err:
        parse(q_string)
    assert str(err.value) == (
        'info:srw/diagnostic/1/10 [Malformed Query]: '
        'Expected Term, got end of query.'
    )
    q_string = '123 any 789 abc'
    with pytest.raises(Diagnostic) as err:
        parse(q_string)
    assert str(err.value) == (
        "info:srw/diagnostic/1/10 [Malformed Query]: "
        "Unprocessed tokens remain: 'abc'"
    )


def test_prefixable_object():
    """Test PrefixableObject."""
    prefix_object = PrefixableObject(query='query')
    assert not prefix_object.resolve_prefix('unknown')
    assert prefix_object.resolve_prefix('cql') == RESERVED_PREFIXES.get('cql')
    prefix_object.add_prefix('name', 'identifier')
    prefix_object.error_on_duplicate_prefix = True
    with pytest.raises(Diagnostic) as err:
        prefix_object.add_prefix('name', 'identifier')
    assert str(err.value) == (
        'info:srw/diagnostic/1/45 [Malformed Query]: name'
    )
    assert prefix_object.resolve_prefix('name') == 'identifier'

    parent_object = PrefixableObject(query='query')
    parent_object.add_prefix('parent_name', 'parent_identifier')
    prefix_object.parent = parent_object
    assert prefix_object.resolve_prefix('parent_name') == 'parent_identifier'
    prefix_object.parent = None

    config_object = PrefixableObject(query='query')
    config_object.add_prefix('config_name', 'config_identifier')
    prefix_object.config = config_object
    assert prefix_object.resolve_prefix('config_name') == 'config_identifier'


def test_prefixed_object():
    """Test PrefixedObject."""
    prefixed_object = PrefixedObject('"TICK.TACK"', query='query')
    assert prefixed_object.prefix == 'tick'
    assert prefixed_object.value == 'tack'
    with pytest.raises(Diagnostic) as err:
        PrefixedObject(".TICK", query='query')
    assert str(err.value) == (
        'info:srw/diagnostic/1/15 [Malformed Query]: Null indexset'
    )
    with pytest.raises(Diagnostic) as err:
        PrefixedObject("TICK.TACK.TOCK", query='query')
    assert str(err.value) == (
        'info:srw/diagnostic/1/15 [Malformed Query]: '
        'Multiple "." characters: tick.tack.tock'
    )

    with pytest.raises(Diagnostic) as err:
        PrefixedObject('"TICK"', query='query',
                       error_on_quoted_identifier=True)
    assert str(err.value) == (
        'info:srw/diagnostic/1/14 [Malformed Query]: "tick"'
    )

    parent = PrefixedObject('TUTU', query='query')
    parent.prefix_uri = 'prefix_tutu'
    prefixed_object.parent = parent
    assert prefixed_object.resolve_prefix() == 'prefix_tutu'
    prefixed_object.prefix_uri = 'prefix_url'
    assert prefixed_object.resolve_prefix() == 'prefix_url'


def test_modifiable_object():
    """Test ModifiableObject."""
    modifiable_object = ModifiableObject()
    assert modifiable_object[0] is None
    assert modifiable_object['type'] is None
    modifier_clause = ModifierClause('type', comp='comparison', val='value',
                                     query='query')
    modifiable_object.modifiers.append(modifier_clause)
    assert modifiable_object[0] == modifier_clause
    assert modifiable_object['type'] == modifier_clause


def test_term():
    """Test Term."""
    with pytest.raises(Diagnostic) as err:
        Term('', query='query', error_on_empty_term=True)
    assert str(err.value) == (
        'info:srw/diagnostic/1/27 [Malformed Query]: '
    )
    with pytest.raises(Diagnostic) as err:
        Term('>=', query='query')
    assert str(err.value) == (
        'info:srw/diagnostic/1/25 [Malformed Query]: >='
    )
    with pytest.raises(Diagnostic) as err:
        Term('^', query='query')
    assert str(err.value) == (
        'info:srw/diagnostic/1/32 [Malformed Query]: '
        'Only anchoring charater(s) in term: ^'
    )
    with pytest.raises(Diagnostic) as err:
        Term('\\\\x\\yz\\', query='query')
    assert str(err.value) == (
        'info:srw/diagnostic/1/26 [Malformed Query]: \\\\x\\yz\\'
    )
