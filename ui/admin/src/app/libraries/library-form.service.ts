import { Injectable } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  Validators,
  FormArray } from '@angular/forms';

import { Library } from './library';
import { TimeValidator } from '../shared/time-validator';
import { LibraryCodeUniqueValidator } from '../shared/library-code-unique-validator';
import { LibrariesService } from './libraries.service';
import { WeekDays } from '../shared/week-days';

@Injectable()
export class LibraryFormService {

  public form;

  private libraryCodeUniqueValidator;

  constructor(
    private fb: FormBuilder,
    private librariesService: LibrariesService
    ) {
      this.libraryCodeUniqueValidator = new LibraryCodeUniqueValidator(
        this.librariesService
      );
      this.build();
  }

  build() {
    this.form = this.fb.group({
      name: ['', [
        Validators.required,
        Validators.minLength(4)
      ]],
      address: ['', Validators.minLength(4)],
      email: ['', Validators.email],
      code: ['', {
        validators: [
          Validators.required
        ],
        asyncValidators: [
          // TODO: Debug multiple call on request
          // this.libraryCodeUniqueValidator.validate.bind(this.libraryCodeUniqueValidator)
        ],
        updateOn: 'blur'
      }],
      opening_hours: this.fb.array(this.createOpeningHours())
    });
  }

  createOpeningHours() {
    const days = Object.keys(WeekDays);
    const openings = [];
    for (let step = 0; step < 7; step++) {
      openings.push(this.buildOpeningHours(false, days[step], this.fb.array([this.buildTimes()])));
    }
    return openings;
  }

  buildOpeningHours(is_open, day, times): FormGroup {
    return this.fb.group({
      is_open: [is_open],
      day: [day],
      times: times
    }, {
      validator: [TimeValidator.RangePeriodValidator()]
    });
  }

  buildTimes(start_time = '00:00', end_time = '00:00'): FormGroup {
    return this.fb.group({
      start_time: [start_time, {
        validators: [
          Validators.required,
          Validators.pattern('^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$')
        ],
        updateOn: 'blur'
      }],
      end_time: [end_time, {
        validators: [
          Validators.required,
          Validators.pattern('^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$')
        ],
        updateOn: 'blur'
      }]
    }, {
      validator: TimeValidator.greaterThanValidator('start_time', 'end_time')
    });
  }

  populate(library: Library) {
    this.form.patchValue({
      name: library.name,
      address:  library.address,
      email: library.email,
      code: library.code,
      opening_hours: library.opening_hours
    });
  }

  setId(id) { this.form.value.id = id; }
  setLibraryPid(pid) { this.form.value.pid = pid; }
  setSchema(schema) { this.form.value.$schema = schema; }

  get name() { return this.form.get('name'); }
  get address() { return this.form.get('address'); }
  get email() { return this.form.get('email'); }
  get code() { return this.form.get('code'); }
  get opening_hours() {
    return <FormArray>this.form.get('opening_hours');
  }

  getValues() { return this.form.value; }

  addTime(day_index): void {
    this.getTimesByDayIndex(day_index).push(this.buildTimes());
  }

  deleteTime(day_index, time_index): void {
    this.getTimesByDayIndex(day_index).removeAt(time_index);
  }

  getTimesByDayIndex(day_index): FormArray {
    return this.form.get('opening_hours')
      .get(String(day_index))
      .get('times') as FormArray;
  }
}
