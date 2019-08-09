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

import { Pipe, PipeTransform } from '@angular/core';
import { TranslateLanguageService } from '../translate/translate-language.service';
import { TranslateService } from '@ngx-translate/core';

@Pipe({ name: 'translateLanguage' })
export class TranslateLanguagePipe implements PipeTransform {

  public constructor(
    public translate: TranslateService,
    public translateLanguageService: TranslateLanguageService
  ) {}

  transform(value: any, args?: any): any {
    return this.translateLanguageService.translate(
      value,
      this.translate.currentLang
    );
  }
}
