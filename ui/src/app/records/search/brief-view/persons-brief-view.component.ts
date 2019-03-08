import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-persons-brief-view',
  template: `
  <h5 class="card-title mb-0 rero-ils-person">
    <a href="{{'/persons/'+record.metadata.pid}}">{{record.metadata | mefTitle}}</a>
      <small *ngIf="record.metadata.rero" class="badge badge-secondary ml-1">RERO</small>
      <small *ngIf="record.metadata.gnd" class="badge badge-secondary ml-1">GND</small>
      <small *ngIf="record.metadata.bnf" class="badge badge-secondary ml-1">BNF</small>
  </h5>
  <div class="card-text px-2">
    <p class="mb-0" *ngIf="record.metadata | birthDate">{{ record.metadata | birthDate }}</p>
    <p class="mb-0" *ngIf="record.metadata | bioInformations">{{ record.metadata | bioInformations }}</p>
  </div>
  `,
  styles: []
})
export class PersonsBriefViewComponent implements BriefView {

  @Input() record: any;

}
