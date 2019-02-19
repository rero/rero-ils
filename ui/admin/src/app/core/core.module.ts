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

@NgModule({
  declarations: [
    AlertsComponent,
    DialogComponent,
    Nl2br
  ],
  imports: [
    CommonModule,
    HttpClientModule,
    AlertModule.forRoot(),
    TranslateModule.forChild({}),
  ],
  providers: [
    ApiService,
    ItemTypeService,
    LibraryService,
    OrganisationService,
    PatronTypeService,
    PatronTypeTool,
    ItemTypeTool,
    UniqueValidator,
    I18nPluralPipe
  ],
  exports: [
    AlertsComponent
  ],
  entryComponents: [
    DialogComponent
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
