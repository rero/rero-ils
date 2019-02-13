import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'birthDate'
})
export class BirthDatePipe implements PipeTransform {

  transform(value: any): any {
    for (const source of ['rero', 'bnf', 'gnd']) {
      if (value[source] && value[source].date_of_birth) {
        return value[source].date_of_birth;
      }
    }
    return null;
  }

}
