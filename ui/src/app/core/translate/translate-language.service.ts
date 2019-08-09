/*

RERO ILS
Copyright (C) 2019 RERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

*/

import { Injectable } from '@angular/core';
import * as I18nIsoLanguages from '@cospired/i18n-iso-languages';

declare const require;

@Injectable()
export class TranslateLanguageService {
  constructor() {
    for (const lang of ['de', 'en', 'fr']) {
      I18nIsoLanguages.registerLocale(
        require('@cospired/i18n-iso-languages/langs/' + lang + '.json')
      );
    }

    /*
    TODO: Missing italian language file on package cospired
    - Remove this after merged this PR https://github.com/cospired/i18n-iso-languages/pull/15
    - Remove directory langs
    - Add the value "it" in the array above
    */
    I18nIsoLanguages.registerLocale(require('./langs/it.json'));
  }

  public translate(isocode: string, language: string) {
    return I18nIsoLanguages.getName(isocode, language);
  }
}
