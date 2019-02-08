import { Component, Input, OnInit } from '@angular/core';
import { BsModalRef } from 'ngx-bootstrap/modal';
import { BsLocaleService } from 'ngx-bootstrap/datepicker';
import { FormArray, FormGroup } from '@angular/forms';
import { Subject } from 'rxjs';

import { LibraryExceptionFormService } from './library-exception-form.service';
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
