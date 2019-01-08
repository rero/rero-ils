import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-persons-brief-view',
  template: `
  <h5><a href="{{'/persons/'+record.metadata.pid}}">{{record.metadata | mefTitle}}</a></h5>
  <h6>
    <span *ngIf="record.metadata.rero" class="badge badge-secondary mr-2">RERO</span>
    <span *ngIf="record.metadata.gnd" class="badge badge-secondary mr-2">GND</span>
    <span *ngIf="record.metadata.bnf" class="badge badge-secondary">BNF</span></h6>
  `,
  styles: []
})
export class PersonsBriefViewComponent implements BriefView {

  @Input() record: any;

}
