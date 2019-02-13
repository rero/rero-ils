import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-locations-brief-view',
  template: `
  <h5 class="mb-0 card-title">{{record.metadata.name}}</h5>
  <div class="card-text">
  {{record.metadata.code}}
  </div>
  `,
  styles: []
})
export class LocationsBriefViewComponent implements BriefView {

  @Input() record: any;

}
