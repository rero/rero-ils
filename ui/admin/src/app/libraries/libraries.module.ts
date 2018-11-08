import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { HttpClientInMemoryWebApiModule } from 'angular-in-memory-web-api';

import { TabsModule } from 'ngx-bootstrap/tabs';
import { UiSwitchModule } from 'ngx-toggle-switch';

import { InMemoryLibrariesDataService } from './in-memory-libraries-data.service';
import { LibrariesRoutingModule } from './libraries-routing.module';
import { LibraryComponent } from './library/library.component';
import { LibraryFormService } from './library-form.service';
import { LibrariesService } from './libraries.service';
import { MainComponent } from './main/main.component';

import { environment } from '../../environments/environment';

@NgModule({
  providers: [
    LibrariesService,
    LibraryFormService
  ],
  declarations: [LibraryComponent, MainComponent],
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
    UiSwitchModule
  ]
})
export class LibrariesModule { }
