import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-patrons-brief-view',
  template: `
  <h5>{{record.metadata.first_name}} {{record.metadata.last_name}} ({{record.metadata.birth_date}})</h5>
  {{record.metadata.roles}}
  `,
  styles: []
})
export class PatronsBriefViewComponent implements BriefView {

  @Input() record: any;

}
