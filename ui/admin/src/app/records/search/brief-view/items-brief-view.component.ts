import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-items-brief-view',
  template: `
  <h5 class="mb-0 card-title">{{record.metadata.barcode}}</h5>
  <div class="card-text">
  {{record.metadata.status}}
  </div>
  `,
  styles: []
})
export class ItemsBriefViewComponent implements BriefView {

  @Input() record: any;

}
