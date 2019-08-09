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

import { NgModule, Optional, SkipSelf } from '@angular/core';
import { CommonModule, I18nPluralPipe } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { AlertModule } from 'ngx-bootstrap/alert';
import { TranslateModule } from '@ngx-translate/core';

import { ItemTypeService } from './item-type/item-type.service';
import { ItemTypeTool } from './item-type/item-type-tool';
import { LibraryService } from './library/library.service';
import { PatronTypeService } from './patron-type/patron-type.service';
import { PatronTypeTool } from './patron-type/patron-type-tool';
import { OrganisationService } from './organisation/organisation.service';
import { ApiService } from './api/api.service';
import { UniqueValidator } from './validator/unique.validator';
import { AlertsComponent } from './alerts/alerts.component';
import { DialogComponent } from './dialog/dialog.component';
import { Nl2br } from './filter/nl2br';
import { ToastrDialogComponent } from './toastr-dialog/toastr-dialog.component';
import { ToastrModule } from 'ngx-toastr';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { TitlePipe } from './pipe/title.pipe';
import { OrganisationViewService } from './organisation/organisation-view.service';
import { TranslateLanguageService } from './translate/translate-language.service';

@NgModule({
  declarations: [
    AlertsComponent,
    DialogComponent,
    Nl2br,
    ToastrDialogComponent,
    TitlePipe
  ],
  imports: [
    CommonModule,
    HttpClientModule,
    AlertModule.forRoot(),
    TranslateModule.forChild({}),
    BrowserAnimationsModule,
    ToastrModule.forRoot({
      toastComponent: ToastrDialogComponent,
      timeOut: 2500
    })
  ],
  providers: [
    ApiService,
    ItemTypeService,
    LibraryService,
    OrganisationService,
    OrganisationViewService,
    PatronTypeService,
    PatronTypeTool,
    ItemTypeTool,
    UniqueValidator,
    I18nPluralPipe,
    TranslateLanguageService
  ],
  exports: [
    AlertsComponent
  ],
  entryComponents: [
    DialogComponent,
    ToastrDialogComponent
  ]
})
export class CoreModule {
  constructor (
    @Optional() @SkipSelf() parentModule: CoreModule
  ) {
    if (parentModule) {
      throw new Error('CoreModule is already loaded. Import only in AppModule');
    }
  }
}
