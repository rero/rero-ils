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

"""Common classes used for documents - identifiers.

Identifiers class represent all possible identifiers data from a document
resource : ISBN, ISSN, EAN, GTIN, DOI, ...

As identifiers are very versatile, we can build a single class to validate or
to normalize them. That is why we will use a factory class to build
any identifier from data. This factory will analyze data to build the best
possible specialized identifier class.

HOW TO USE :

   >> from rero_ils.modules.documents.commons import *
   >> data = {
   >>    'type': 'bf:Isbn',
   >>    'value': '9782844267788',
   >>    'qualifier: 'tome 2'
   >> }
   >> identifier = IdentifierFactory.createIdentifier(data)
   >> print(s.render(render_class=QualifierIdentifierRenderer())

To render an identifier in a specialized way, a `render class` can be used to
render this identifier in the expected way. In the previous example, we will
use the `QualifierIdentifierRenderer` ; the result will be
"9782844267788, tome 2"

"""
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Optional, TypeVar

from isbnlib import NotValidISBNError, canonical, ean13, is_isbn10, mask, \
    notisbn, to_isbn10, to_isbn13


class InvalidIdentifierException(Exception):
    """Exception if an identifier is invalid."""


class IdentifierType:
    """Type of identifier."""

    AUDIO_ISSUE_NUMBER = 'bf:AudioIssueNumber'
    DOI = 'bf:Doi'
    EAN = 'bf:Ean'
    GTIN_14 = 'bf:Gtin14Number'
    IDENTIFIER = 'bf:Identifier'
    ISAN = 'bf:Isan'
    ISBN = 'bf:Isbn'
    ISMN = 'bf:Ismn'
    ISRC = 'bf:Isrc'
    ISSN = 'bf:Issn'
    L_ISSN = 'bf:IssnL'
    LCCN = 'bf:Lccn'
    LOCAL = 'bf:Local'
    MATRIX_NUMBER = 'bf:MatrixNumber'
    MUSIC_DISTRIBUTOR_NUMBER = 'bf:MusicDistributorNumber'
    MUSIC_PLATE = 'bf:MusicPlate'
    MUSIC_PUBLISHER_NUMBER = 'bf:MusicPublisherNumber'
    PUBLISHER_NUMBER = 'bf:PublisherNumber'
    UPC = 'bf:Upc'
    URN = 'bf:Urn'
    VIDEO_RECORDING_NUMBER = 'bf:VideoRecordingNumber'
    URI = 'uri'


class IdentifierStatus:
    """Status of identifier."""

    UNDEFINED = None
    INVALID = 'invalid'
    CANCELLED = 'cancelled'
    INVALID_OR_CANCELLED = 'invalid or cancelled'

    ALL = [
        UNDEFINED,
        INVALID,
        CANCELLED,
        INVALID_OR_CANCELLED
    ]


# =============================================================================
#     IDENTIFIER
# =============================================================================
#    * `Identifier` class is the most generic class for a document identifier.
#    * `ISBNIdentifier` class represent any ISBN identifier (isbn-10, isbn-13)
#    * `EANIdentifier` class to represent an isbn without any hyphens
# =============================================================================
DocIdentifier = TypeVar('DocIdentifier')


@dataclass(repr=False)
class Identifier:
    """Generic document identifier representation."""

    value: str
    type: Optional[str] = None
    note: Optional[str] = None
    qualifier: Optional[str] = None
    source: Optional[str] = None
    status: str = field(default=IdentifierStatus.UNDEFINED)

    def __post_init__(self):
        """Post initialization dataclass magic function."""
        if self.status == IdentifierStatus.UNDEFINED and not self.is_valid():
            self.status = IdentifierStatus.INVALID
        if hasattr(self, '__type__'):
            self.type = self.__type__
        if not self.type:
            raise InvalidIdentifierException("'type' is a required property.")

    def __hash__(self) -> int:
        """Get a hash value for this identifier."""
        return hash(self.type + self.value)

    def __eq__(self, other) -> bool:
        """Check if an identifier equals to another identifier."""
        self_hash = hash(self.type + self.normalize())
        other_hash = hash(self.type + self.normalize())
        return self_hash == other_hash

    def __str__(self) -> str:
        """Get simple string representation of the identifier."""
        return self.normalize()

    def to_dict(self):
        """Expose identifier as a dictionary."""
        data = self.__dict__
        data.pop('__type__', None)
        return data

    def normalize(self) -> str:
        """Get the normalized value of the identifier."""
        return self.value

    def is_valid(self) -> bool:
        """Check if the identifier is valid."""
        # As we are in a generic class, all identifier are valid.
        return True

    def validate(self) -> None:
        """Validate the identifier."""
        # same as `is_valid` but raise an exception if the identifier isn't
        # valid
        if not self.is_valid():
            raise InvalidIdentifierException()

    def dump(self) -> dict:
        """Dump this identifier."""
        status = self.status if self.is_valid() else IdentifierStatus.INVALID
        data = {
            'type': self.type,
            'value': self.normalize(),
            'note': self.note,
            'qualifier': self.qualifier,
            'source': self.source,
            'status': status
        }
        return {k: v for k, v in data.items() if v}

    def render(self, **kwargs) -> str:
        """Render the identifier.

        :param kwargs: all possible named argument to render this identifier.
           * 'render_class': the rendering class to use to get the identifier
                             representation.
        :return: the string representation of the identifier.
        """
        render_class = kwargs.pop('render_class', DefaultIdentifierRenderer())
        return render_class.render(self, **kwargs)

    def get_alternatives(self) -> list[DocIdentifier]:
        """Get a list of alternative for this identifier."""
        # a generic identifier doesn't have any alternatives
        return []


@dataclass(unsafe_hash=True)
class ISBNIdentifier(Identifier):
    """ISBN document identifier."""

    __type__: str = field(default=IdentifierType.ISBN, repr=False)

    def __str__(self) -> str:
        """Get simple string representation for this ISBN (with hyphens)."""
        try:
            return mask(self.normalize())
        except NotValidISBNError:
            return self.value

    def normalize(self) -> str:
        """Get the normalized value for this ISBN."""
        return canonical(self.value) or self.value

    def is_valid(self) -> bool:
        """Check if the identifier is valid."""
        return not notisbn(self.value)

    def get_alternatives(self) -> list[Identifier]:
        """Get a list of alternative for this identifiers."""
        alternatives = []
        transform_func = to_isbn13 if is_isbn10(self.value) else to_isbn10
        if alternate_isbn := transform_func(self.value):
            data = deepcopy(self)
            data.value = alternate_isbn
            data.type = IdentifierType.ISBN
            alternatives.append(ISBNIdentifier(**data.to_dict()))
        if ean_value := ean13(self.value):
            data = deepcopy(self)
            data.value = ean_value
            data.type = IdentifierType.EAN
            alternatives.append(EANIdentifier(**data.to_dict()))
        return alternatives


@dataclass(unsafe_hash=True)
class EANIdentifier(Identifier):
    """ISBN document identifier."""

    __type__: str = field(default=IdentifierType.EAN, repr=False)

    def normalize(self) -> str:
        """Get the normalized value for this EAN."""
        return canonical(self.value) or self.value
    __str__ = normalize

    def is_valid(self) -> bool:
        """Check if the identifier is valid."""
        return bool(canonical(self.value))

    def get_alternatives(self) -> list[Identifier]:
        """Get a list of alternative for this identifier."""
        alternatives = []
        for identifier in (to_isbn10(self.value), to_isbn13(self.value)):
            if identifier:
                data = deepcopy(self)
                data.value = identifier
                data.type = IdentifierType.ISBN
                alternatives.append(ISBNIdentifier(**data.to_dict()))
        return alternatives


# =============================================================================
#     RENDERING
# =============================================================================
#   Classes below allows to render an identifier in a specific way.
#   Usage is mainly the same than `dumps()` method from any Invenio resource :
#
#   identifier = Identifier(type='bf:Isbn', value='xxxx', qualifier='t.2')
#   print(identifier.render())  // in this case we use the default renderer
#   >> xxx
#   print(identifier.render(render_class=QualifierIdentifierRenderer())
#   >> xxx, t.2
# =============================================================================

class IdentifierRenderer(ABC):
    """Identifier renderer class."""

    @abstractmethod
    def render(self, identifier: Identifier, **kwargs) -> str:
        """Get the string representation of an identifier."""
        raise NotImplementedError()


class DefaultIdentifierRenderer(IdentifierRenderer):
    """Default identifier renderer class."""

    def render(self, identifier: Identifier, **kwargs) -> str:
        """Get the string representation of an identifier."""
        return str(identifier)


class QualifierIdentifierRenderer(IdentifierRenderer):
    """Identifier renderer class including the qualifier attribute."""

    def render(self, identifier: Identifier, **kwargs) -> str:
        """Get the string representation of an identifier."""
        output = str(identifier)
        if identifier.qualifier:
            output += f', {identifier.qualifier}'
        return output


# =============================================================================
#     FACTORY
# =============================================================================

class IdentifierFactory:
    """Factory to build `Identifier` object from dictionary."""

    _mapping_table = {
        IdentifierType.ISBN: ISBNIdentifier,
        IdentifierType.EAN: EANIdentifier
    }

    @staticmethod
    def create_identifier(data) -> Identifier:
        """Factory method to create the concrete identifier class.

        :param data: the dictionary representing the identifier.
        :return the created Identifier.
        """
        if 'type' not in data:
            raise AttributeError("'type' is a required property.")

        if data['type'] in IdentifierFactory._mapping_table:
            return IdentifierFactory._mapping_table[data['type']](**data)
        return Identifier(**data)
