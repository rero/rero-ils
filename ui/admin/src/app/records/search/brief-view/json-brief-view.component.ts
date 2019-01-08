import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-json-brief-view',
  template: `
  {{ record | json }}
  `,
  styles: []
})
export class JsonBriefViewComponent implements BriefView {

  @Input() record: any;

}
