# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Normalized sort for rero-ils."""

import re


class NormalizerStopWords():
    """Normalizer Stop words."""

    stop_words_punctuation = []
    stop_words_regex = {}

    def __init__(self, app=None):
        """Init."""
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        if app.config.get('RERO_ILS_STOP_WORDS_ACTIVATE', False):
            self.init_config(app)
            app.extensions['reroils-normalizer-stop-words'] = self

    def init_config(self, app):
        """Initialize configuration."""
        punc = app.config.get('RERO_ILS_STOP_WORDS_PUNCTUATION', [])
        self.stop_words_punctuation = '|'.join(punc)
        stop_words = app.config.get('RERO_ILS_STOP_WORDS', {})
        if stop_words:
            # Generating a regex per language
            for lang, words in stop_words.items():
                self.stop_words_regex[lang] = \
                     r'\b(' + r'|'.join(words) + r')\b\s*'

    def normalize(self, text, language=None):
        """Normalize.

        :param text: Text to be normalized
        :param language: Language of the text
        :returns: Normalized text
        """
        word_regex = self.stop_words_regex.get(
            language,
            self.stop_words_regex.get('default')
        )
        if word_regex:
            compiled = re.compile(fr'{word_regex}', re.IGNORECASE)
            text = compiled.sub('', text)
        if self.stop_words_punctuation:
            compiled = re.compile(
                fr'{self.stop_words_punctuation}', re.IGNORECASE)
            text = compiled.sub('', text)
        return re.sub(r'\s+', ' ', text).strip()
