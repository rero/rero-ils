import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-libraries-brief-view',
  template: `
  <h5>{{record.metadata.name}}</h5>
  {{record.metadata.code}}
  `,
  styles: []
})
export class LibrariesBriefViewComponent implements BriefView {

  @Input() record: any;

}
