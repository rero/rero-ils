import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-items-brief-view',
  template: `
  <h5>{{record.metadata.barcode}}</h5>
  {{record.metadata.status}}
  `,
  styles: []
})
export class ItemsBriefViewComponent implements BriefView {

  @Input() record: any;

}
