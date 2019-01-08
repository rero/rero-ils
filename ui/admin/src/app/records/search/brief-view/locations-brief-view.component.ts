import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-locations-brief-view',
  template: `
  <h5>{{record.metadata.name}}</h5>
  {{record.metadata.code}}
  `,
  styles: []
})
export class LocationsBriefViewComponent implements BriefView {

  @Input() record: any;

}
