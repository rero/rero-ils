import { AbstractControl } from '@angular/forms';
import { RecordsService } from '@app/records/records.service';

export class UniqueValidator {
  static createValidator(
    recordsService: RecordsService,
    recordType: string,
    fieldName: string,
    excludePid: number = null
  ) {
    return (control: AbstractControl) => {
      return recordsService.valueAlreadyExists(
        recordType,
        fieldName,
        control.value,
        excludePid
      );
    };
  }
}
