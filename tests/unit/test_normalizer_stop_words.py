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

"""Normalizer stop words tests."""

from rero_ils.modules.normalizer_stop_words import NormalizerStopWords


def test_normalize(app):
    """Test stop words normalize."""
    # ---- The string is not analyzed
    app.config["RERO_ILS_STOP_WORDS_ACTIVATE"] = False
    normalizer = NormalizerStopWords(app)
    text = "L'été a été très chaud."
    assert text == normalizer.normalize(text)

    # ---- The string is analyzed
    app.config["RERO_ILS_STOP_WORDS_ACTIVATE"] = True
    app.config["RERO_ILS_STOP_WORDS_PUNCTUATION"] = [
        '"',
        ",",
        ";",
        ":",
        r"\.",
        "_",
        r"\?",
        r"\!",
        r"\*",
        r"\+",
        "\n",
    ]
    normalizer = NormalizerStopWords(app)
    text = "L'été a été très chaud."
    text_norm = "L'été a été très chaud"
    # The language is not defined. Removal of punctuation only.
    assert text_norm == normalizer.normalize(text)

    # Deleting words for the defined language.
    text_norm = "été a été très chaud"
    app.config["RERO_ILS_STOP_WORDS"] = {
        "fre": ["de", "des", "du", "l'", "la", "le", "les", "un", "une"]
    }
    assert text_norm == normalizer.normalize(text, "fre")

    text = (
        "Journal des tribunaux : jurisprudence fédérale. "
        "4, Droit pénal et procédure pénale"
    )
    text_norm = (
        "Journal tribunaux jurisprudence fédérale 4 Droit pénal et procédure pénale"
    )
    assert text_norm == normalizer.normalize(text, "fre")

    # The language was not found in the definition of stop words.
    text = "He plays this musical phrase quite well."
    text_norm = "He plays this musical phrase quite well"
    assert text_norm == normalizer.normalize(text, "eng")

    # Deleting words with the default definition.
    text = "L'été a été très chaud."
    text_norm = "été a été chaud"
    app.config["RERO_ILS_STOP_WORDS"] = {"default": ["l'", "très"]}
    normalizer = NormalizerStopWords(app)
    assert text_norm == normalizer.normalize(text, "und")
