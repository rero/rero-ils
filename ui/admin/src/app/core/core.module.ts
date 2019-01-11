import { NgModule, Optional, SkipSelf } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';

import { ItemTypeService } from './item-type/item-type.service';
import { ItemTypeTool } from './item-type/item-type-tool';
import { LibraryService } from './library/library.service';
import { PatronTypeService } from './patron-type/patron-type.service';
import { PatronTypeTool } from './patron-type/patron-type-tool';
import { OrganisationService } from './organisation/organisation.service';
import { ApiService } from './api/api.service';
import { UniqueValidator } from './validator/unique.validator';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    HttpClientModule,
  ],
  providers: [
    ApiService,
    ItemTypeService,
    LibraryService,
    OrganisationService,
    PatronTypeService,
    PatronTypeTool,
    ItemTypeTool,
    UniqueValidator
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
