import { Component, Inject, Input, LOCALE_ID, OnInit } from '@angular/core';
import { BsModalRef } from 'ngx-bootstrap/modal';
import { BsLocaleService } from 'ngx-bootstrap/datepicker';
import { FormArray, FormGroup } from '@angular/forms';
import * as moment from 'moment';

import { LibraryExceptionFormService } from '../library-exception-form.service';
import { LibrariesService } from '../libraries.service';
import { Library } from '../library';

@Component({
  selector: 'libraries-exception-dates-edit',
  templateUrl: './exception-dates-edit.component.html',
  styleUrls: ['./exception-dates-edit.component.scss']
})
export class ExceptionDatesEditComponent implements OnInit {

  @Input() index: number;
  public exceptionForm: FormGroup;
  public library: Library;

  constructor(
      public localeService: BsLocaleService,
      public bsModalRef: BsModalRef,
      public form: LibraryExceptionFormService,
      public librariesService: LibrariesService,
      @Inject(LOCALE_ID) locale
  ) {
    this.form.build();
    this.exceptionForm = this.form.form;
    this.localeService.use(locale);
  }

  ngOnInit() {
    this.librariesService.currentLibrary.subscribe(
      library => {
        this.library = library;
        if (this.index !== null) {
          this.form.populate(this.library.exception_dates[this.index]);
        }
      }
    );
  }

  onSubmit(index) {
    this.dateException(index, this.exceptionForm.value);
    this.bsModalRef.hide();
  }

  onCancel() {
    this.bsModalRef.hide();
    return false;
  }

  onPeriodChange(period) {
    this.form.is_period.setValue(period);
    if (period) {
      for (let i = 0; i < this.form.times.length; i++) {
        this.form.times.removeAt(i);
      }
      this.form.is_open.setValue(false);
    }
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

  formatDateException(data) {
    const data_exception = {
      title: data.title,
      is_open: data.is_open,
    };
    if (data.is_period) {
      data_exception['start_date'] = moment(data.dates[0]).format('YYYY-MM-DD');
      data_exception['end_date'] = moment(data.dates[1]).format('YYYY-MM-DD');
    } else {
      data_exception['start_date'] = moment(data.date).format('YYYY-MM-DD');
    }
    if (data.times.length > 0) {
      data_exception['times'] = data.times;
    }
    if (data.repeat) {
      data_exception['repeat'] = {
        interval: data.interval,
        period: data.period
        // data: data.repeat.data
      };
    }
    return data_exception;
  }

  dateException(index, data) {
    data = this.formatDateException(data);
    if (index === null) {
      this.library.addException(data);
    } else {
      this.library.updateException(index, data);
    }
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
