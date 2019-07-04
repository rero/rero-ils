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

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { RecordsRoutingModule } from './records-routing.module';
import { MainComponent } from './main/main.component';
import { SearchComponent } from './search/search.component';

import { SharedModule } from '../shared.module';

import { UiSwitchModule } from 'ngx-toggle-switch';
import { TabsModule } from 'ngx-bootstrap/tabs';
import { Bootstrap4FrameworkModule } from 'angular6-json-schema-form';

import { EditorComponent } from './editor/editor.component';
import { RemoteSelectComponent } from './editor/remote-select/remote-select.component';
import { RemoteInputComponent } from './editor/remote-input/remote-input.component';
import { BriefViewDirective } from './search/brief-view/brief-view.directive';
import { JsonBriefViewComponent } from './search/brief-view/json-brief-view.component';
import { ResultComponent } from './search/result/result.component';
import { ItemTypesBriefViewComponent } from './search/brief-view/item-types-brief-view.component';
import { PatronTypesBriefViewComponent } from './search/brief-view/patron-types-brief-view.component';
import { CircPoliciesBriefViewComponent } from './search/brief-view/circ-policies-brief-view.component';
import { PatronsBriefViewComponent } from './search/brief-view/patrons-brief-view.component';
import { PersonsBriefViewComponent } from './search/brief-view/persons-brief-view.component';
import { LibrariesBriefViewComponent } from './search/brief-view/libraries-brief-view.component';
import { DocumentsBriefViewComponent } from './search/brief-view/documents-brief-view.component';
import { PublicDocumentsBriefViewComponent } from './search/brief-view/public-documents-brief-view.component';
import { ExceptionDatesListComponent } from './custom-editor/libraries/exception-dates-list/exception-dates-list.component';
import { ExceptionDatesEditComponent } from './custom-editor/libraries/exception-dates-edit/exception-dates-edit.component';
import { BsDatepickerModule } from 'ngx-bootstrap/datepicker';
import { ModalModule } from 'ngx-bootstrap/modal';
import { LibraryExceptionFormService } from './custom-editor/libraries/library-exception-form.service';
import { MefTitlePipe } from './search/brief-view/mef-title.pipe';
import { CirculationPolicyComponent } from './custom-editor/circulation-settings/circulation-policy/circulation-policy.component';
import { CirculationPolicyService } from './custom-editor/circulation-settings/circulation-policy.service';
import { CirculationPolicyFormService } from './custom-editor/circulation-settings/circulation-policy-form.service';
import { CirculationMappingService } from './custom-editor/circulation-settings/circulation-mapping.service';
import { LibraryComponent } from './custom-editor/libraries/library.component';
import { LibraryFormService } from './custom-editor/libraries/library-form.service';
import { BirthDatePipe } from './search/brief-view/birth-date.pipe';
import { BioInformationsPipe } from './search/brief-view/bio-informations.pipe';
import { CollapseModule } from 'ngx-bootstrap/collapse';
import { AdminSearchComponent } from './search/admin-search/admin-search.component';
import { PublicSearchComponent } from './search/public-search/public-search.component';
import { DocumentsSearchComponent } from './search/public-search/documents-search.component';
import { PersonsSearchComponent } from './search/public-search/persons-search.component';
import { RefAuthorityComponent } from './editor/ref-authority/ref-authority.component';
import { TypeaheadModule } from 'ngx-bootstrap/typeahead';
import { RolesCheckboxesComponent } from './editor/roles-checkboxes/roles-checkboxes.component';
import { AggregationComponent } from './search/aggregation/aggregation.component';

@NgModule({
  declarations: [
    MainComponent,
    SearchComponent,
    EditorComponent,
    RemoteSelectComponent,
    RemoteInputComponent,
    BriefViewDirective,
    JsonBriefViewComponent,
    ResultComponent,
    ItemTypesBriefViewComponent,
    PatronTypesBriefViewComponent,
    CircPoliciesBriefViewComponent,
    PatronsBriefViewComponent,
    LibrariesBriefViewComponent,
    DocumentsBriefViewComponent,
    PublicDocumentsBriefViewComponent,
    ExceptionDatesListComponent,
    ExceptionDatesEditComponent,
    PersonsBriefViewComponent,
    MefTitlePipe,
    CirculationPolicyComponent,
    LibraryComponent,
    BirthDatePipe,
    BioInformationsPipe,
    AdminSearchComponent,
    PublicSearchComponent,
    DocumentsSearchComponent,
    PersonsSearchComponent,
    RefAuthorityComponent,
    RolesCheckboxesComponent,
    AggregationComponent
  ],
  imports: [
    CommonModule,
    RecordsRoutingModule,
    SharedModule,
    Bootstrap4FrameworkModule,
    FormsModule, ReactiveFormsModule,
    UiSwitchModule,
    ModalModule.forRoot(),
    BsDatepickerModule.forRoot(),
    TabsModule.forRoot(),
    CollapseModule.forRoot(),
    TypeaheadModule.forRoot()
  ],
  entryComponents: [
    RemoteSelectComponent,
    RolesCheckboxesComponent,
    RemoteInputComponent,
    RefAuthorityComponent,
    JsonBriefViewComponent,
    ItemTypesBriefViewComponent,
    PatronTypesBriefViewComponent,
    CircPoliciesBriefViewComponent,
    PatronsBriefViewComponent,
    LibrariesBriefViewComponent,
    DocumentsBriefViewComponent,
    PublicDocumentsBriefViewComponent,
    ExceptionDatesListComponent,
    ExceptionDatesEditComponent,
    PersonsBriefViewComponent
  ],
  providers: [
    LibraryExceptionFormService,
    CirculationPolicyService,
    CirculationPolicyFormService,
    CirculationMappingService,
    LibraryFormService
  ]
})
export class RecordsModule { }
