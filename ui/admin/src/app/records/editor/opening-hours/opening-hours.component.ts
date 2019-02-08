import { FormArray, FormGroup, FormBuilder, Validators } from '@angular/forms';
import { Component, Input, OnInit } from '@angular/core';
import { JsonSchemaFormService } from 'angular6-json-schema-form';
import { TimeValidator } from '../../../shared/time-validator';

@Component({
  selector: 'app-opening-hours',
  templateUrl: './opening-hours.component.html',
  styleUrls: ['./opening-hours.component.scss']
})
export class OpeningHoursComponent implements OnInit {

  formControl: FormArray;
  controlName: string;
  controlValue: any[];
  controlDisabled = false;
  boundControl = false;
  options: any;
  @Input() layoutNode: any;
  @Input() layoutIndex: number[];
  @Input() dataIndex: number[];

  constructor(
    private jsf: JsonSchemaFormService,
    private fb: FormBuilder
    ) { }

  ngOnInit() {
    this.options = this.layoutNode.options || {};
    this.jsf.initializeControl(this);
    const days = <FormArray>this.formControl;
    days.controls.map(
      (day: FormGroup) => {
        const times = <FormArray>day.get('times');
        times.controls.map(
          (time: FormGroup) => {
            time.setValidators([TimeValidator.greaterThanValidator('start_time', 'end_time')]);
            time.get('start_time').setValidators([
              Validators.required,
              Validators.pattern('^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$')
            ]);
            time.get('end_time').setValidators([
              Validators.required,
              Validators.pattern('^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$')
            ]);
        });
        day.setValidators([TimeValidator.RangePeriodValidator()]);
    });
  }

  addTime(i: number) {
    const timesCtrl = this.formControl.controls[i].get('times') as FormArray;
    timesCtrl.push(this.buildTimes());
  }

  updateValue(event) {
    this.jsf.updateValue(this, event.target.value);
  }

  buildTimes(start_time = '00:00', end_time = '00:00'): FormGroup {
    return this.fb.group({
      start_time: [start_time, {
        validators: [
          Validators.required,
          Validators.pattern('^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$')
        ]
      }],
      end_time: [end_time, {
        validators: [
          Validators.required,
          Validators.pattern('^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$')
        ]
      }]
    }, {
      validator: TimeValidator.greaterThanValidator('start_time', 'end_time')
    });
  }

  deleteTime(day_index, time_index): void {
    this.getTimesByDayIndex(day_index).removeAt(time_index);
  }

  getTimesByDayIndex(day_index): FormArray {
    return this.formControl
    .get(String(day_index))
    .get('times') as FormArray;
  }
}
