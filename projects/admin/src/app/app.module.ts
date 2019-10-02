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

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { AppConfigService } from './app-config.service';
import { MenuComponent } from './menu/menu.component';
import { UserService } from './services/user.service';
import { HttpClientModule } from '@angular/common/http';
import { CollapseModule } from 'ngx-bootstrap';
import { FrontpageComponent } from './frontpage/frontpage.component';

@NgModule({
  declarations: [
    AppComponent,
    MenuComponent,
    FrontpageComponent
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    CoreModule,
    SharedModule,
    RecordModule,
    HttpClientModule,
    CollapseModule.forRoot()
  ],
  providers: [
    {
      provide: CoreConfigService,
      useClass: AppConfigService
    },
    UserService
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
