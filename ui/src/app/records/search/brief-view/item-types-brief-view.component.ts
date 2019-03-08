import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-item-types-brief-view',
  template: `
  <h5 class="mb-0 card-title">{{record.metadata.name}}</h5>
  <div class="card-text">
    <span *ngIf="record.metadata.description">
      {{record.metadata.description}}
    </span>
  </div>
  `,
  styles: []
})
export class ItemTypesBriefViewComponent implements BriefView {

  @Input() record: any;

}
