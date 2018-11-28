import { Injectable } from '@angular/core';
import {
  FormBuilder,
  FormControl,
  FormGroup,
  Validators,
  FormArray } from '@angular/forms';
import { Library } from './library';

@Injectable()
export class LibraryFormService {

  public form;

  constructor(private fb: FormBuilder) {
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
      code: [''],
      opening_hours: this.fb.array([this.buildOpeningHours()]),
    });
  }

  buildOpeningHours(): FormGroup {
    return this.fb.group({
      is_open: [''],
      day: [''],
      times: this.fb.array([this.buildTimes()])
    });
  }

  buildTimes(): FormGroup {
    return this.fb.group({
      start_time: ['00:00', [ Validators.required ]],
      end_time: ['00:00', [ Validators.required ]]
    });
  }


  populate(library: Library) {
    this.form.patchValue({
      name: library.name,
      address:  library.address,
      email: library.email,
      code: library.code
    });

    const openings = new FormArray([]);
    library.opening_hours.forEach(opening => {
      const hours = new FormArray([]);
      if (opening.times.length === 0) {
        opening.times.push({
          start_time: '00:00',
          end_time: '00:00'
        });
      }
      opening.times.forEach(time => {
        hours.push(this.fb.group({
          start_time: time.start_time,
          end_time: time.end_time
        }));
      });
      openings.push(this.fb.group({
        day: opening.day,
        is_open: opening.is_open,
        times: hours
      }));
    });
    this.form.setControl('opening_hours', openings);
  }

  setId(id) { this.form.value.id = id; }
  setLibraryPid(pid) { this.form.value.pid = pid; }
  setSchema(schema) { this.form.value.$schema = schema; }

  get name() { return this.form.get('name'); }
  get address() { return this.form.get('address'); }
  get email() { return this.form.get('email'); }
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
