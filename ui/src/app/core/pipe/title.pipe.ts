import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'title'
})
export class TitlePipe implements PipeTransform {

  transform(value: any, args?: any): any {
    return value.substring(0, 1).toUpperCase() + value.substring(1);
  }
}
