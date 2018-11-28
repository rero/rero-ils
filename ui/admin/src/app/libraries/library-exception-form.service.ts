import { Injectable } from '@angular/core';
import { FormBuilder, FormGroup, Validators} from '@angular/forms';
import * as moment from 'moment';

@Injectable()
export class LibraryExceptionFormService {

  public form;

  constructor( private fb: FormBuilder ) {
    this.build();
  }

  build() {
    this.form = this.fb.group({
      title: ['', [ Validators.required ]],
      date: [moment().toDate(), [ Validators.required ]],
      dates: [
        [moment().toDate(), moment().toDate()],
        [ Validators.required ]
      ],
      is_period: [false, [ Validators.required ]],
      is_open: [false, [ Validators.required ]],
      times: this.fb.array([]),
      repeat: [false],
      interval: [null],
      period: [null],
      data: this.fb.array([])
    });
  }

  buildTimes(start_time = '00:00', end_time = '00:00'): FormGroup {
    return this.fb.group({
      start_time: [start_time, [ Validators.required ]],
      end_time: [end_time, [ Validators.required ]]
    });
  }

  buildRepeat(): FormGroup {
    return this.fb.group({
      interval: ['', [ Validators.required ]],
      period: ['', [ Validators.required ]],
      data: ['']
    });
  }

  populate(exception) {
    this.title.setValue(exception.title);
    if ('end_date' in exception) {
      this.is_period.setValue(true);
      this.dates.setValue([
        moment(exception.start_date, 'YYYY-MM-DD').toDate(),
        moment(exception.end_date, 'YYYY-MM-DD').toDate(),
      ]);
    } else {
      this.date.setValue(moment(exception.start_date, 'YYYY-MM-DD').toDate());
    }
    this.is_open.setValue(exception.is_open);
    if ('times' in exception) {
      exception.times.forEach(
        time => {
          this.times.push(this.buildTimes(time.start_time, time.end_time));
        }
      );
    }
    if ('repeat' in exception) {
      this.repeat.setValue(true);
      this.period.setValue(exception.repeat.period);
      this.interval.setValue(exception.repeat.interval);
      // this.data.setValue(exception.repeat.data)
    }
  }

  get title() { return this.form.get('title'); }
  get is_period() { return this.form.get('is_period'); }
  get is_open() { return this.form.get('is_open'); }
  get date() { return this.form.get('date'); }
  get dates() { return this.form.get('dates'); }
  get times() { return this.form.get('times'); }
  get repeat() { return this.form.get('repeat'); }
  get interval() { return this.form.get('interval'); }
  get period() { return this.form.get('period'); }
  get data() { return this.form.get('data'); }

}
