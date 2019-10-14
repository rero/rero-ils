/*
 * RERO ILS UI
 * Copyright (C) 2019 RERO
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import { TranslateLoader as NgCoreTranslateLoader } from '@rero/ng-core';
import { AppConfigService } from '../../service/app-config.service';

import fr from '../i18n/fr.json';
import de from '../i18n/de.json';
import en from '../i18n/en.json';
import it from '../i18n/it.json';

export class TranslateLoader extends NgCoreTranslateLoader {

  /**
   * Store translations in available languages.
   */
  private applicationTranslations: object = { fr, de, en, it };

  /**
   * Constructor
   * @param config - ConfigService, invenio core configuration
   */
  constructor(private appService: AppConfigService) {
    super(appService);
    this.loadApplicationTranslations();
  }

  /**
   * Load application translations
   */
  private loadApplicationTranslations() {
    for (const lang of this.appService.languages) {
      this.translations[lang] = {...this.translations[lang], ...this.applicationTranslations[lang]};
    }
  }
}
