import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'bioInformations'
})
export class BioInformationsPipe implements PipeTransform {

  transform(value: any): any {
    for (const source of ['rero', 'bnf', 'gnd']) {
      if (value[source] && value[source].biographical_information) {
        return value[source].biographical_information;
      }
    }
    return null;
  }

}
