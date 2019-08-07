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

import { Component, Input, OnInit } from '@angular/core';
import { BsModalRef } from 'ngx-bootstrap/modal';
import { BsLocaleService } from 'ngx-bootstrap/datepicker';
import { FormArray, FormGroup } from '@angular/forms';
import { Subject } from 'rxjs';

import { LibraryExceptionFormService } from '../library-exception-form.service';
import { TranslateService } from '@ngx-translate/core';

@Component({
  selector: 'libraries-exception-dates-edit',
  templateUrl: './exception-dates-edit.component.html',
  styleUrls: ['./exception-dates-edit.component.scss']
})
export class ExceptionDatesEditComponent implements OnInit {

  @Input() exceptionDate: any;
  value = new Subject();
  public exceptionForm: FormGroup;

  constructor(
    public localeService: BsLocaleService,
    public bsModalRef: BsModalRef,
    public form: LibraryExceptionFormService,
    private translate: TranslateService
    ) {
    this.form.build();
    this.exceptionForm = this.form.form;
    this.localeService.use(this.translate.currentLang);
  }

  ngOnInit() {
    if (this.exceptionDate) {
      this.form.populate(this.exceptionDate);
    }
  }

  onSubmit() {
    this.bsModalRef.hide();
    this.value.next(this.form.getValue());
  }

  onCancel() {
    this.bsModalRef.hide();
  }

  onPeriodChange(event) {
    const target = event.target;
    const value = target.value === 'true';
    this.form.is_period.setValue(value);
    if (value) {
      for (let i = 0; i < this.form.times.length; i++) {
        this.form.times.removeAt(i);
      }
      this.form.is_open.setValue(false);
    }
  }

  onDateStatusChange(event) {
    const target = event.target;
    const value = target.value === 'true';
    this.form.is_open.setValue(value);
  }

  onRepeatChange(repeat) {
    if (repeat) {
      this.form.interval.setValue(1);
      this.form.period.setValue('yearly');
    } else {
      this.form.interval.setValue(null);
      this.form.period.setValue(null);
    }
  }

  addTime(): void {
    this.form.times.push(this.form.buildTimes());
  }

  deleteTime(time_index): void {
    this.form.times.removeAt(time_index);
  }

  get title() { return this.form.title; }
  get is_period() { return this.form.is_period; }
  get is_open() { return this.form.is_open; }
  get date() { return this.form.date; }
  get dates() { return this.form.dates; }
  get times() { return <FormArray>this.form.times; }
  get repeat() { return this.form.repeat; }
  get interval() { return this.form.interval; }
  get period() { return this.form.period; }
  get data() { return <FormArray>this.data; }
}
