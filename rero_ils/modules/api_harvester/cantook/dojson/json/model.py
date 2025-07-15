# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
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

"""Cantook json record transformation."""

import dateparser

from rero_ils.modules.documents.models import DocumentFictionType
from rero_ils.modules.utils import get_schema_for_resource

CONTRIBUTION_NATURE = {
    "adapted_by": "adp",
    "afterword_by": "aft",
    "author": "aut",
    "by_composer": "cmp",
    "by_photographer": "pht",
    "cover_design_or_artwork_by": "ill",
    "director": "drt",
    "drawings_by": "ill",
    "edited_by": "edt",
    "editor_in_chief": "edt",
    "editorial_coordination_by": "edt",
    "epilogue_by": "aft",
    "foreword_by": "aui",
    "general_editor": "edt",
    "illustrator": "ill",
    "instrumental_soloist": "mus",
    "interviewer": "ivr",
    "introduction_and_notes_by": "aui",
    "introduction_by": "aui",
    "maps_by": "ctg",
    "narrator": "nrt",
    "other": "oth",
    "other_primary_creator": "cre",
    "photograph": "pht",
    "preface_by": "aui",
    "read_by": "nrt",
    "screenplay_by": "aus",
    "selected_by": "cur",
    "series_edited_by": "pbl",
    "translated_by": "trl",
    "volume_editor": "pbl",
}


class Transformation:
    """Transformation CANTOOK Json to RERO-ILS Json."""

    def __init__(self, data=None, logger=None, verbose=False, transform=True):
        """Constructor."""
        self.data = data
        self.logger = logger
        self.verbose = verbose
        self.json_dict = {}
        if data and transform:
            self._transform()

    def _transform(self):
        """Call the transformation functions."""
        for func in dir(self):
            if func.startswith("trans_"):
                func = getattr(self, func)
                func()

    def do(self, data):
        """Do the transformation.

        :param data: json data to transform
        :returns: rero-ils document data
        """
        self.data = data
        self._transform()
        return self.json_dict

    @property
    def json(self):
        """Json data."""
        return self.json_dict or None

    def trans_constants(self):
        """Add constants."""
        self.json_dict["$schema"] = get_schema_for_resource("doc")
        self.json_dict["harvested"] = True
        self.json_dict["issuance"] = {
            "main_type": "rdami:1001",
            "subtype": "materialUnit",
        }
        self.json_dict["adminMetadata"] = {"encodingLevel": "Not applicable"}
        self.json_dict["type"] = [
            {"main_type": "docmaintype_book", "subtype": "docsubtype_e-book"}
        ]

    def trans_pid(self):
        """Transformation pid."""
        self.json_dict["pid"] = f"cantook-{self.data['id']}"

    def trans_identified_by(self):
        """Transformation IdentifiedBy."""
        identified_by = [
            {
                "source": "CANTOOK",
                "type": "bf:Local",
                "value": f"cantook-{self.data['id']}",
            }
        ]
        for media in self.data.get("media", []):
            nature = media.get("nature")
            if nature in ["paper", "epub", "audio"] and media["key_type"] == "isbn13":
                identified_by.append(
                    {"type": "bf:Isbn", "value": media.get("key"), "note": nature}
                )
            if nature == "audio":
                self.json_dict["type"] = [
                    {
                        "main_type": "docmaintype_audio",
                        "subtype": "docsubtype_audio_book",
                    }
                ]
        self.json_dict["identifiedBy"] = identified_by

    def trans_title(self):
        """Transformation Title."""
        title = {"type": "bf:Title"}
        if maintitle := self.data.get("title"):
            title["mainTitle"] = [{"value": maintitle}]
        if subtitle := self.data.get("subtitle"):
            title["subtitle"] = [{"value": subtitle}]
        self.json_dict["title"] = [title]

    def trans_contribution(self):
        """Transformation Contribution."""
        contributions = []
        for contribution in self.data.get("contributors", []):
            nature = contribution["nature"]
            role = CONTRIBUTION_NATURE.get(nature, "ctb")

            names = []
            if last_name := contribution.get("last_name"):
                names.append(last_name)
            if first_name := contribution.get("first_name"):
                names.append(first_name)

            entity = {
                "role": [role],
                "entity": {
                    "authorized_access_point": ", ".join(names),
                    "type": "bf:Person",
                },
            }
            if entity not in contributions:
                contributions.append(entity)
        if contributions:
            self.json_dict["contribution"] = contributions

    def trans_provision_activity(self):
        """Transform provisionActivity."""
        publisher_name = self.data.get("publisher_name", "Publisher unknown")
        start_date = dateparser.parse(self.data.get("created_at", "1990-01-01"))
        self.json_dict["provisionActivity"] = [
            {
                "startDate": start_date.year,
                "statement": [
                    {"label": [{"value": publisher_name}], "type": "bf:Agent"},
                    {"label": [{"value": str(start_date.year)}], "type": "Date"},
                ],
                "type": "bf:Publication",
            }
        ]

    def trans_electronic_locator(self):
        """Transformation electronicLocator."""
        electronic_locators = []
        if cover := self.data.get("cover"):
            electronic_locators.append(
                {
                    "content": "coverImage",
                    "type": "relatedResource",
                    "url": cover,
                }
            )
        if flipbook := self.data.get("flipbook"):
            electronic_locators.append(
                {
                    "content": "extract",
                    "type": "relatedResource",
                    "url": flipbook,
                }
            )
        if electronic_locators:
            self.json_dict["electronicLocator"] = electronic_locators

    def trans_fiction(self):
        """Transformation fiction."""
        if self.data.get("fiction"):
            self.json_dict["fiction_statement"] = DocumentFictionType.Fiction.value
        self.json_dict["fiction_statement"] = DocumentFictionType.Unspecified.value

    def trans_language(self):
        """Transformation language."""
        if languages := [
            {"type": "bf:Language", "value": language}
            for language in self.data.get("languages", [])
        ]:
            self.json_dict["language"] = languages

    def trans_orginal_language(self):
        """Transformation language."""
        if language := self.data.get("translated_from"):
            self.json_dict["originalLanguage"] = [language]

    # def trans_subjects(self):
    #     """Transformation Subject."""
    #     use_standard = ["cantook"]  # feedbooks, thema, bisac
    #     subjects = []
    #     for classification in self.data.get("classifications", []):
    #         if classification.get("standard") in use_standard:
    #             for caption in classification.get("captions", []):
    #                 if subject := caption.get("fr"):
    #                     subjects.append(
    #                         {
    #                             "entity": {
    #                                 "authorized_access_point": subject,
    #                                 "type": "bf:Topic",
    #                             }
    #                         }
    #                     )
    #     if subjects:
    #         self.json_dict["subjects"] = subjects

    def trans_summary(self):
        """Transformation Summary."""
        if summary := self.data.get("summary"):
            self.json_dict["summary"] = [{"label": [{"value": summary}]}]

    def trans_extent(self):
        """Transformation Extend."""
        if page_count := self.data.get("page_count"):
            self.json_dict["extent"] = f"{page_count} pages"

    # to be used to create holdings
    def trans_links(self):
        """Transformation links."""
        if link := self.data.get("link"):
            self.json_dict["link"] = link

    # to be used for deleted records
    def trans_deleted(self):
        """Transformation deleted."""
        if unavailable_since := self.data.get("unavailable_since"):
            self.json_dict["deleted"] = unavailable_since


cantook_json = Transformation()
