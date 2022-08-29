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

"""Common classes used for documents - subjects.

Subjects class represent all possible subjects data from a document resource.
It exists two kinds of subject: local subjects and references subjects.
  * A local subject is a data structure where all subject metadata are include
    in the self structure.
  * A referenced subject is a data structure where a `$ref` key is a link to an
    URI where found some metadata.

HOW TO USE :

   >> from rero_ils.modules.documents.commons import Subject, SubjectFactory
   >> Subject s = SubjectFactory.createSubject(subject_data)
   >> print(s.render(language='fre'))

As we don't know (we don't want to know) which kind of subject as describe into
`subject` data, we can't use the specialized corresponding class. Instead, we
can use a factory class that build for us the correct subject.
So we NEVER need to use other classes than `Subject` and `SubjectFactory`.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from rero_ils.modules.contributions.api import Contribution
from rero_ils.modules.contributions.utils import \
    get_contribution_localized_value
from rero_ils.modules.documents.models import DocumentSubjectType


# =============================================================================
# SUBJECT CLASSES
# =============================================================================
@dataclass
class Subject(ABC):
    """Document subject representation."""

    type: str = field(init=False)
    data: dict = field(default_factory=dict)

    def __post_init__(self):
        """Post initialization dataclass magic function."""
        if 'type' not in self.data:
            raise AttributeError('"type" attribute is required')
        self.type = self.data['type']

    @abstractmethod
    def render(self, **kwargs) -> str:
        """Render the subject as a string."""
        raise NotImplementedError()


@dataclass
class ReferenceSubject(Subject):
    """Document subject related to a reference URI."""

    reference: str = field(init=False)

    def __post_init__(self):
        """Post initialization dataclass magic function."""
        super().__post_init__()
        if '$ref' not in self.data:
            raise AttributeError('"$ref" attribute is required')
        self.reference = self.data['$ref']

    def render(self, language=None, **kwargs) -> str:
        """Render the subject as a string.

        :param language: preferred language for the subject.
        :return the string representation of this subject.
        """
        sub, _, _ = Contribution.get_record_by_ref(self.reference)
        return sub.get_authorized_access_point(language=language)


@dataclass
class ResolvedReferenceSubject(Subject):
    """Document subject related to a resolved reference URI."""

    def __post_init__(self):
        """Post initialization dataclass magic function."""
        super().__post_init__()
        if 'sources' not in self.data:
            raise AttributeError('"sources" attribute is required')

    def render(self, language=None, **kwargs) -> str:
        """Render the subject as a string.

        :param language: preferred language for the subject.
        :return the string representation of this subject.
        """
        return get_contribution_localized_value(
            contribution=self.data,
            key='authorized_access_point',
            language=language)


@dataclass
class LocalSubject(Subject, ABC):
    """Local document subject."""

    part_separator: str = ' - '

    def _get_subdivision_terms(self) -> list[str]:
        """Get subject subdivision terms.

        :return the subdivision terms list.
        """
        return self.data.get('genreForm_subdivisions', []) \
            + self.data.get('topic_subdivisions', []) \
            + self.data.get('temporal_subdivisions', []) \
            + self.data.get('place_subdivisions', [])

    @abstractmethod
    def get_main_label(self) -> str:
        """Get the main label of the subject."""
        raise NotImplementedError()

    def render(self, **kwargs) -> str:
        """Render the subject as a string.

        :return the best possible label for this subject.
        """
        parts = [self.get_main_label()] + self._get_subdivision_terms()
        return LocalSubject.part_separator.join(parts)


@dataclass
class TermLocalSubject(LocalSubject):
    """Local document subject representing base on `term` field."""

    def get_main_label(self) -> str:
        """Get the main label of the subject."""
        if 'term' not in self.data:
            raise AttributeError('"term" doesn\'t exist for this subject')
        return self.data['term']


@dataclass
class PreferredNameLocalSubject(LocalSubject):
    """Local document subject representing base on `preferred_name` field."""

    def get_main_label(self) -> str:
        """Get the main label of the subject."""
        if 'preferred_name' not in self.data:
            msg = '"preferred_name" doesn\'t exist for this subject'
            raise AttributeError(msg)
        return self.data['preferred_name']


@dataclass
class TitleLocalSubject(LocalSubject):
    """Local document subject representing base on `title` field."""

    def get_main_label(self) -> str:
        """Get the main label of the subject."""
        if 'title' not in self.data:
            msg = '"title" doesn\'t exist for this subject'
            raise AttributeError(msg)
        parts = [self.data['title']]
        if 'creator' in self.data:
            parts.append(self.data['creator'])
        return ' / '.join(parts)


# =============================================================================
# SUBJECT FACTORIES
# =============================================================================

class SubjectFactory:
    """Document subject factory."""

    @staticmethod
    def create_subject(data) -> Subject:
        """Factory method to create the concrete subject class.

        :param data: the dictionary representing the subject.
        :return the created subject.
        """
        factory_class = LocalSubjectFactory
        if '$ref' in data:
            factory_class = ReferenceSubjectFactory
        if 'sources' in data:
            factory_class = ResolvedReferenceSubjectFactory
        return factory_class()._build_subject(data)

    @abstractmethod
    def _build_subject(self, data) -> Subject:
        """Build a subject from data.

        :param data: the dictionary representing the subject.
        :return the built subject.
        """
        raise NotImplementedError


class ReferenceSubjectFactory(SubjectFactory):
    """Document referenced subject factory."""

    def _build_subject(self, data) -> ReferenceSubject:
        """Build a subject from data.

        :param data: the dictionary representing the subject.
        :return the built subject.
        """
        return ReferenceSubject(data=data)


class ResolvedReferenceSubjectFactory(SubjectFactory):
    """Document referenced subject factory."""

    def _build_subject(self, data) -> ResolvedReferenceSubject:
        """Build a subject from data.

        :param data: the dictionary representing the subject.
        :return the built subject.
        """
        return ResolvedReferenceSubject(data=data)


class LocalSubjectFactory(SubjectFactory):
    """Document local subject factory."""

    mapper = {
        DocumentSubjectType.ORGANISATION: PreferredNameLocalSubject,
        DocumentSubjectType.PERSON: PreferredNameLocalSubject,
        DocumentSubjectType.PLACE: PreferredNameLocalSubject,
        DocumentSubjectType.TEMPORAL: TermLocalSubject,
        DocumentSubjectType.TOPIC: TermLocalSubject,
        DocumentSubjectType.WORK: TitleLocalSubject,
    }

    def _build_subject(self, data) -> Subject:
        """Build a subject from data.

        :param data: the dictionary representing the subject.
        :return the built subject.
        """
        subject_type = data.get('type')
        if subject_type not in self.mapper.keys():
            raise AttributeError(f'{subject_type} isn\'t a valid subject type')
        return self.mapper[subject_type](data=data)
