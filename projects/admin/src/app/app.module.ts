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
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';

import { NgModule } from '@angular/core';

import { RecordModule, CoreModule, CoreConfigService, SharedModule } from '@rero/ng-core';
import { UiSwitchModule } from 'ngx-toggle-switch';
import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { AppConfigService } from './service/app-config.service';
import { MenuComponent } from './menu/menu.component';
import { UserService } from './service/user.service';
import { HttpClientModule } from '@angular/common/http';
import { CollapseModule, TabsModule, BsDatepickerModule } from 'ngx-bootstrap';
import { FrontpageComponent } from './frontpage/frontpage.component';
import { ItemTypesBriefViewComponent } from './record/brief-view/item-types-brief-view.component';
import { CircPoliciesBriefViewComponent } from './record/brief-view/circ-policies-brief-view.component';
import { DocumentsBriefViewComponent } from './record/brief-view/documents-brief-view.component';
import { LibrariesBriefViewComponent } from './record/brief-view/libraries-brief-view.component';
import { PatronTypesBriefViewComponent } from './record/brief-view/patron-types-brief-view.component';
import { PatronsBriefViewComponent } from './record/brief-view/patrons-brief-view.component';
import { PersonsBriefViewComponent } from './record/brief-view/persons-brief-view.component';
import { BioInformationsPipe } from './pipe/bio-informations.pipe';
import { BirthDatePipe } from './pipe/birth-date.pipe';
import { MefTitlePipe } from './pipe/mef-title.pipe';
import { LibraryComponent } from './record/custom-editor/libraries/library.component';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { ExceptionDatesListComponent } from './record/custom-editor/libraries/exception-dates-list/exception-dates-list.component';
import { ExceptionDatesEditComponent } from './record/custom-editor/libraries/exception-dates-edit/exception-dates-edit.component';
import { CirculationPolicyComponent } from './record/custom-editor/circulation-settings/circulation-policy/circulation-policy.component';

@NgModule({
  declarations: [
    AppComponent,
    MenuComponent,
    FrontpageComponent,
    ItemTypesBriefViewComponent,
    CircPoliciesBriefViewComponent,
    DocumentsBriefViewComponent,
    LibrariesBriefViewComponent,
    PatronTypesBriefViewComponent,
    PatronsBriefViewComponent,
    PersonsBriefViewComponent,
    BioInformationsPipe,
    BirthDatePipe,
    MefTitlePipe,
    LibraryComponent,
    ExceptionDatesListComponent,
    ExceptionDatesEditComponent,
    CirculationPolicyComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    CoreModule,
    SharedModule,
    RecordModule,
    HttpClientModule,
    CollapseModule.forRoot(),
    FormsModule,
    ReactiveFormsModule,
    TabsModule.forRoot(),
    UiSwitchModule,
    BsDatepickerModule
  ],
  providers: [
    {
      provide: CoreConfigService,
      useClass: AppConfigService
    },
    UserService
  ],
  entryComponents: [
    ItemTypesBriefViewComponent,
    CircPoliciesBriefViewComponent,
    DocumentsBriefViewComponent,
    LibrariesBriefViewComponent,
    PatronTypesBriefViewComponent,
    PatronsBriefViewComponent,
    PersonsBriefViewComponent
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
