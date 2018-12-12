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
import { LocationsBriefViewComponent } from './search/brief-view/locations-brief-view.component';
import { LibrariesBriefViewComponent } from './search/brief-view/libraries-brief-view.component';
import { ItemsBriefViewComponent } from './search/brief-view/items-brief-view.component';
import { DocumentsBriefViewComponent } from './search/brief-view/documents-brief-view.component';
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
    LocationsBriefViewComponent,
    LibrariesBriefViewComponent,
    ItemsBriefViewComponent,
    DocumentsBriefViewComponent,
    ExceptionDatesListComponent,
    ExceptionDatesEditComponent,
    PersonsBriefViewComponent,
    MefTitlePipe,
    CirculationPolicyComponent,
    LibraryComponent
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

  ],
  entryComponents: [
    RemoteSelectComponent,
    RemoteInputComponent,
    JsonBriefViewComponent,
    ItemTypesBriefViewComponent,
    PatronTypesBriefViewComponent,
    CircPoliciesBriefViewComponent,
    PatronsBriefViewComponent,
    LocationsBriefViewComponent,
    LibrariesBriefViewComponent,
    ItemsBriefViewComponent,
    DocumentsBriefViewComponent,
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
