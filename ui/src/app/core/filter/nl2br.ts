import { PipeTransform, Pipe } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';

@Pipe({ name: 'nl2br'})
export class Nl2br implements PipeTransform {

  public constructor(public sanitizer: DomSanitizer) {}

  transform(value: string): any {
    return this.sanitizer.bypassSecurityTrustHtml(
      value.replace(/\n/g, '<br>\n')
    );
  }
}
