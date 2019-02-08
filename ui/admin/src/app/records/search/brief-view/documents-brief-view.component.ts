import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-documents-brief-view',
  template: `
  <h5><a href="{{'/documents/' + record.metadata.pid}}">{{record.metadata.title}}</a></h5>
  <span *ngFor="let author of record.metadata.authors; let isLast=last">
      {{ author.name }} {{isLast ? '' : ', '}}
  </span>

  <p>
    <a
      class="btn"
      data-toggle="collapse"
      href="#{{'items-'+record.metadata.pid}}"
      role="button"
      aria-expanded="false"
      aria-controls="collapseExample"
    >
      <i class="fa fa-caret-down" aria-hidden="true"></i>
    </a>
    <span *ngIf="record.metadata.items">{{record.metadata.items.length}}</span> items
     <a
      class="ml-3 text-secondary float-right"
      routerLinkActive="active"
      [queryParams]="{document: record.metadata.pid}"
      [routerLink]="['/records/items/new']"
    >
      <i class="fa fa-plus" aria-hidden="true"></i>
    </a>
  </p>

  <div class="collapse" id="{{'items-'+record.metadata.pid}}">
    <div class="card card-body border-0 py-0">
      <ul *ngIf="record.metadata.items" class="list-group list-group-flush">
        <li *ngFor="let item of record.metadata.items "class="list-group-item">
          <a href="{{'/items/' + item.pid }}">{{item.barcode}} ({{item.status}})</a>
          <a
            *ngIf="recordType !== 'persons'"
            (click)="deleteItem(item.pid)"
            class="ml-3 float-right text-secondary"
          >
            <i class="fa fa-trash" aria-hidden="true"></i>
          </a>
          <a
            *ngIf="recordType !== 'persons'"
            class="ml-3 float-right text-secondary"
            routerLinkActive="active"
            [routerLink]="['/records/items', item.pid]"
            [queryParams]="{document: record.metadata.pid}"
          >
            <i class="fa fa-pencil" aria-hidden="true"></i>
          </a>
        </li>
      </ul>
    </div>
  </div>
  `,
  styles: []
})
export class DocumentsBriefViewComponent implements BriefView {

  @Input() record: any;

  deleteItem(pid) {
    // TODO: Not implemented ?
    console.log(pid);
  }

}
