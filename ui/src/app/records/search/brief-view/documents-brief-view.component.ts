import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';
import { RecordsService } from '../../records.service';

import { _, AlertsService } from '@app/core';


@Component({
  selector: 'app-documents-brief-view',
  template: `
  <h5 class="mb-0 card-title"><a href="{{'/documents/' + record.metadata.pid}}">{{record.metadata.title}}</a>
  <small> &ndash; {{ record.metadata.type | translate }}</small></h5>
  <div class="card-text">
  <span *ngFor="let publisher of record.metadata.publishers; let isLast=last">
    <span *ngIf="publisher.name">
      {{ publisher.name }}{{isLast ? '. ' : ', '}}
    </span>
  </span>
  <span *ngIf="record.metadata.freeFormedPublicationDate; else PublicationYear">
    {{ record.metadata.freeFormedPublicationDate }}
    </span>
    <ng-template #PublicationYear>{{ record.metadata.publicationYear }}</ng-template>
  </div>
  <section *ngIf="record.metadata.type != 'ebook'">
    <a *ngIf="record.metadata.items && record.metadata.items.length"
       class="collapsed text-secondary" data-toggle="collapse"
       href="#{{'items-'+record.metadata.pid}}"
       aria-expanded="false" aria-controls="itemsList">
      <i class="fa fa-caret-down" aria-hidden="true"></i> <span translate> items</span>
    </a>
    <span *ngIf="!(record.metadata.items && record.metadata.items.length)" translate>no item</span>
     <a class="ml-2 text-secondary" routerLinkActive="active"
        [queryParams]="{document: record.metadata.pid}" [routerLink]="['/records/items/new']">
      <i class="fa fa-plus" aria-hidden="true"></i> {{ 'Add' | translate }}
    </a>
  </section>
  <ul *ngIf="record.metadata.items"
      class="collapse list-group list-group-flush"
      id="{{'items-'+record.metadata.pid}}">
    <li *ngFor="let item of record.metadata.items "class="list-group-item p-1">
      <a href="{{'/items/' + item.pid }}">{{item.barcode}}</a><span> ({{ item.status | translate }})</span>
      <a *ngIf="recordType !== 'persons'" (click)="deleteItem(item.pid)"
         class="ml-2 float-right text-secondary" title="{{ 'Delete' | translate }}">
        <i class="fa fa-trash" aria-hidden="true"></i>
      </a>
      <a *ngIf="recordType !== 'persons'" class="ml-2 float-right text-secondary"
         routerLinkActive="active"
         [routerLink]="['/records/items', item.pid]"
         [queryParams]="{document: record.metadata.pid}"
         title="{{ 'Edit' | translate }}">
        <i class="fa fa-pencil" aria-hidden="true"></i>
      </a>
    </li>
  </ul>
  `,
  styles: []
})
export class DocumentsBriefViewComponent implements BriefView {

  @Input() record: any;

  constructor(
    private recordsService: RecordsService,
    private alertsService: AlertsService
    ) {}

  deleteItem(pid) {
    this.recordsService.deleteRecord(pid, 'items').subscribe(success => {
      if (success) {
        this.record.metadata.items = this.record.metadata.items.filter(item => item.pid !== pid);
        this.alertsService.addAlert('warning', _('Record deleted.'));
      }
    });
  }

}
