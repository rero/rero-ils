import { AbstractControl, ValidatorFn, FormArray } from '@angular/forms';
import * as moment from 'moment';

export class TimeValidator {
  static greaterThanValidator(start: string, end: string): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } => {
      if (control) {
        let isLessThan = false;
        const startTime = control.get('start_time');
        const endTime = control.get('end_time');
        const startDate = moment(startTime.value, 'HH:mm');
        const endDate = moment(endTime.value, 'HH:mm');
        if (startDate.format('HH:mm') !== '00:00' || endDate.format('HH:mm') !== '00:00') {
          isLessThan = startDate.diff(endDate) >= 0;
        }
        return isLessThan ? { lessThan: { value: isLessThan }} : null;
      }
    };
  }

  static RangePeriodValidator(): ValidatorFn {
    return (control: AbstractControl): { [key: string]: any } => {
      if (control.value) {
        let isRangeLessThan = false;
        const times = <FormArray>control.get('times');
        if (control.get('is_open').value && times.value.length > 1) {
          const firstStartDate = moment(times.at(0).get('start_time').value, 'HH:mm');
          const firstEndDate = moment(times.at(0).get('end_time').value, 'HH:mm');
          const lastStartDate = moment(times.at(1).get('start_time').value, 'HH:mm');
          const lastEndDate = moment(times.at(1).get('end_time').value, 'HH:mm');
          if (firstStartDate > lastStartDate) {
            isRangeLessThan = firstStartDate.diff(lastStartDate) <= 0
              || firstStartDate.diff(lastEndDate) <= 0;
          } else {
            isRangeLessThan = lastStartDate.diff(firstEndDate) <= 0
              || lastStartDate.diff(firstEndDate) <= 0;
          }
        }
        return isRangeLessThan ? { rangeLessThan: { value: isRangeLessThan} } : null;
      }
    };
  }
}
