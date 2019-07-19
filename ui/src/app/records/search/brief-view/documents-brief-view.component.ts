import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';
import { RecordsService } from '../../records.service';
import { TranslateService } from '@ngx-translate/core';
import { ToastrService } from 'ngx-toastr';
import { _ } from '@app/core';


@Component({
  selector: 'app-documents-brief-view',
  template: `
  <h5 class="mb-0 card-title"><a href="{{ '/' + viewCode + '/documents/' + record.metadata.pid }}">{{ record.metadata.title }}</a>
  <small> &ndash; {{ record.metadata.type | translate }}</small></h5>
  <div class="card-text">

  <!-- author -->
  <ul class="list-inline mb-0" *ngIf="record.metadata.authors && record.metadata.authors.length > 0">
    <li class="list-inline-item" *ngFor="let author of record.metadata.authors.slice(0,3); let last = last">
      <span *ngIf="!author.pid">
        {{ authorName(author) }}
        {{ author.qualifier ? author.qualifier : '' }}
        {{ author.date ? author.date : '' }}
      </span>
      <a *ngIf="author.pid" href="/{{ viewCode }}/persons/{{ author.pid }}">
        {{ authorName(author) }}
        {{ author.qualifier ? author.qualifier : '' }}
        {{ author.date ? author.date : '' }}
      </a>
      {{ last ? '' : '; ' }}

    </li>
    <li *ngIf="record.metadata.authors && record.metadata.authors.length > 3">; …</li>
  </ul>

  <span *ngFor="let publisher of record.metadata.publishers; let isLast=last">
    <span *ngIf="publisherNames()">
      {{ publisherNames() }}{{isLast ? '. ' : ', '}}
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
  </section>
  <ul *ngIf="record.metadata.items"
      class="collapse list-group list-group-flush"
      id="{{'items-'+record.metadata.pid}}">
    <li *ngFor="let item of record.metadata.items "class="list-group-item p-1">
      <a href="{{'/' + viewCode + '/items/' + item.pid }}">{{item.barcode}}</a><span> ({{ item.status | translate }})</span>
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

  // Find a better way to fix this
  // Another edit view for admin ???
  public viewCode = 'global';

  constructor(
    private recordsService: RecordsService,
    private translate: TranslateService,
    private toastService: ToastrService
    ) {}

  publisherNames() {
    const name_index = `name_${this.translate.currentLang}`;
    const publishers = [];
    for (const publisher of this.record.metadata.publishers) {
      let name_lng = publisher[name_index];
      if (!name_lng) {
        name_lng = publisher['name'];
      }
      publishers.push(name_lng);
    }
    return publishers;
  }

  authorName(author) {
    const name_index = `name_${this.translate.currentLang}`;
    let name_lng = author[name_index];
    if (!name_lng) {
      name_lng = author['name'];
    }
    return name_lng;
  }

  deleteItem(pid) {
    this.recordsService.deleteRecord(pid, 'items').subscribe(success => {
      if (success) {
        this.record.metadata.items = this.record.metadata.items.filter(item => item.pid !== pid);
        this.toastService.success(_('Record deleted.'), _('documents'));
      }
    });
  }

}
