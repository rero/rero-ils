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

import { ExceptionDatesEditComponent } from './exception-dates-edit.component';
import { CommonModule } from '@angular/common';
import { CoreModule, SharedModule } from '@rero/ng-core';
import { BsDatepickerModule, BsModalRef } from 'ngx-bootstrap';
import { LOCALE_ID } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { UiSwitchModule } from 'ngx-toggle-switch';

describe('ExceptionDatesEditComponent', () => {
  let component: ExceptionDatesEditComponent;
  let fixture: ComponentFixture<ExceptionDatesEditComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExceptionDatesEditComponent ],
      imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        CoreModule,
        SharedModule,
        UiSwitchModule,
        BsDatepickerModule.forRoot()
      ],
      providers: [BsModalRef, {provide: LOCALE_ID, useValue: 'en-US' }]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExceptionDatesEditComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
