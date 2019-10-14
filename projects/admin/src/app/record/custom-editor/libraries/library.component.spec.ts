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

import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LibraryComponent } from './library.component';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CoreModule, SharedModule } from '@rero/ng-core';
import { TabsModule, BsDatepickerModule } from 'ngx-bootstrap';
import { UiSwitchModule } from 'ngx-toggle-switch';
import { ExceptionDatesListComponent } from './exception-dates-list/exception-dates-list.component';
import { ExceptionDatesEditComponent } from './exception-dates-edit/exception-dates-edit.component';
import { HttpClientModule } from '@angular/common/http';
import { RouterTestingModule } from '@angular/router/testing';

describe('LibraryComponent', () => {
  let component: LibraryComponent;
  let fixture: ComponentFixture<LibraryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        ExceptionDatesListComponent,
        ExceptionDatesEditComponent,
        LibraryComponent ],
      imports: [
        FormsModule,
        ReactiveFormsModule,
        CoreModule,
        SharedModule,
        TabsModule.forRoot(),
        UiSwitchModule,
        BsDatepickerModule.forRoot(),
        HttpClientModule,
        RouterTestingModule
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LibraryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
