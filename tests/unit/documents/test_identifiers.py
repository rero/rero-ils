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

"""Tests identifier classes for documents."""

import pytest

from rero_ils.modules.commons.identifiers import (
    Identifier,
    IdentifierFactory,
    IdentifierStatus,
    IdentifierType,
    InvalidIdentifierException,
    QualifierIdentifierRenderer,
)


def test_identifiers_creation():
    """Test identifiers creation using factory or direct object creation."""
    data = {"type": IdentifierType.URI, "value": "http://valid.url"}
    assert IdentifierFactory.create_identifier(data)
    assert Identifier(**data)

    data = {"value": "http://valid.url.but.no.type"}
    with pytest.raises(AttributeError):
        IdentifierFactory.create_identifier(data)
    with pytest.raises(InvalidIdentifierException):
        Identifier(**data)


def test_isbn_identifiers():
    """Test ISBN identifiers."""
    # VALID ISBN IDENTIFIER
    data = {"type": IdentifierType.ISBN, "value": "978-284426778-8"}
    identifier = IdentifierFactory.create_identifier(data)
    assert identifier.is_valid()
    assert str(identifier) == "978-2-84426-778-8"
    assert identifier.normalize() == "9782844267788"
    assert len(identifier.get_alternatives()) == 2  # ISBN-10 and EAN
    assert hash(identifier)

    # INVALID ISBN IDENTIFIER
    data = {"type": IdentifierType.ISBN, "value": "978-284426778-X"}
    identifier = IdentifierFactory.create_identifier(data)
    assert not identifier.is_valid()
    assert identifier.status == IdentifierStatus.INVALID
    # unable to normalize an invalid ISBN --> normalize() and str() will return
    # the original value
    assert identifier.normalize() == "978-284426778-X"
    assert str(identifier) == "978-284426778-X"
    with pytest.raises(InvalidIdentifierException):
        identifier.validate()
    assert len(identifier.get_alternatives()) == 0


def test_ean_identifiers():
    """Test EAN identifiers."""
    data = {"type": IdentifierType.EAN, "value": "9782844267788"}
    identifier = IdentifierFactory.create_identifier(data)
    assert identifier.is_valid()
    assert str(identifier) == "9782844267788"
    assert identifier.normalize() == "9782844267788"
    assert len(identifier.get_alternatives()) == 2  # ISBN-10 and ISBN-13


def test_identifiers_renderer():
    """Test identifiers renderer."""
    data = {
        "type": IdentifierType.ISBN,
        "value": "978-284426778-8",
        "qualifier": "tome 2",
    }
    identifier = IdentifierFactory.create_identifier(data)
    assert identifier.render() == "978-2-84426-778-8"
    assert (
        identifier.render(render_class=QualifierIdentifierRenderer())
        == "978-2-84426-778-8, tome 2"
    )
