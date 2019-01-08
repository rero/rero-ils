import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { HttpClientInMemoryWebApiModule } from 'angular-in-memory-web-api';
import { TranslateModule } from '@ngx-translate/core';

import { ModalModule } from 'ngx-bootstrap/modal';
import { TabsModule } from 'ngx-bootstrap/tabs';
import { UiSwitchModule } from 'ngx-ui-switch';
import { BsDatepickerModule } from 'ngx-bootstrap/datepicker';

import { InMemoryLibrariesDataService } from './in-memory-libraries-data.service';
import { LibrariesRoutingModule } from './libraries-routing.module';
import { LibraryComponent } from './library/library.component';
import { LibraryFormService } from './library-form.service';
import { LibraryExceptionFormService } from './library-exception-form.service';

import { LibrariesService } from './libraries.service';
import { MainComponent } from './main/main.component';

import { environment } from '../../environments/environment';
import { ExceptionDatesListComponent } from './exception-dates-list/exception-dates-list.component';
import { ExceptionDatesEditComponent } from './exception-dates-edit/exception-dates-edit.component';

@NgModule({
  providers: [
    LibrariesService,
    LibraryExceptionFormService,
    LibraryFormService
  ],
  declarations: [
    ExceptionDatesEditComponent,
    ExceptionDatesListComponent,
    LibraryComponent,
    MainComponent
  ],
  imports: [
    CommonModule,
    LibrariesRoutingModule,
    HttpClientModule,
    // the dataEncapsulation configuration default changed from false to true.
    // The HTTP response body holds the data values directly rather than an object
    // that encapsulates those values, {data: ...}.
    // the put204 configuration control whether PUT and POST return the saved entity
    // It is true by default which means they do not return the entity
    environment.production ? [] : HttpClientInMemoryWebApiModule.forRoot(
      InMemoryLibrariesDataService, { dataEncapsulation: false, put204: false }
    ),
    ReactiveFormsModule,
    TabsModule.forRoot(),
    UiSwitchModule,
    ModalModule.forRoot(),
    BsDatepickerModule.forRoot(),
    TranslateModule
  ],
  entryComponents: [ ExceptionDatesEditComponent ],
})
export class LibrariesModule { }
