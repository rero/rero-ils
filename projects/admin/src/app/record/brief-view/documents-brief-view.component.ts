/*
 * RERO ILS UI
 * Copyright (C) 2019 RERO
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import { Component, Input } from '@angular/core';
import { ResultItem, RecordService } from '@rero/ng-core';
import { TranslateService } from '@ngx-translate/core';
import { ToastrService } from 'ngx-toastr';
import { UserService } from '../../service/user.service';
import { marker as _ } from '@biesbjerg/ngx-translate-extract-marker';

@Component({
  selector: 'admin-documents-brief-view',
  template: `
  <h5 class="mb-0 card-title">{{ record.metadata.title }}
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
        <a *ngIf="author.pid" href="#">
          {{ authorName(author) }}
          {{ author.qualifier ? author.qualifier : '' }}
          {{ author.date ? author.date : '' }}
        </a>
        {{ last ? '' : '; ' }}

      </li>
      <li *ngIf="record.metadata.authors && record.metadata.authors.length > 3">; …</li>
    </ul>

    <!-- publisher_statements -->
    <span *ngIf="record.metadata.publisherStatement">
      {{ record.metadata.publisherStatement[0] }}
    </span>
  </div>
  <section *ngIf="!record.metadata.harvested">
    <button *ngIf="countHoldingsItems()"
       class="btn btn-link"
       (click)="isItemsCollapsed = !isItemsCollapsed"
       aria-expanded="false" aria-controls="itemsList">
      <i [ngClass]="{'fa-caret-down':!isItemsCollapsed, 'fa-caret-right': isItemsCollapsed}" class="fa" aria-hidden="true"></i>
      <span translate *ngIf="countHoldingsItems() == 1"> item</span>
      <span translate *ngIf="countHoldingsItems() > 1"> items</span>
    </button>
    <span *ngIf="!countHoldingsItems()" translate>no item</span>
  </section>
  <ul *ngIf="countHoldingsItems() > 0"
      class="list-group list-group-flush"
      [collapse]="isItemsCollapsed">
    <li *ngFor="let item of groupItems() "class="list-group-item p-1">
      <a href="#">{{item.barcode}}</a><span> ({{ item.status | translate }})</span>
      <a (click)="deleteItem(item.pid)"
         class="ml-2 float-right text-secondary" title="{{ 'Delete' | translate }}">
        <i class="fa fa-trash" aria-hidden="true"></i>
      </a>
      <a class="ml-2 float-right text-secondary"
         routerLinkActive="active"
         [routerLink]="['/records/items/edit', item.pid]"
         [queryParams]="{document: record.metadata.pid}"
         title="{{ 'Edit' | translate }}">
        <i class="fa fa-pencil" aria-hidden="true"></i>
      </a>
    </li>
  </ul>
  `,
  styles: []
})
export class DocumentsBriefViewComponent implements ResultItem {

  @Input()
  record: any;

  @Input()
  type: string;

  isItemsCollapsed = true;

  constructor(
    private recordsService: RecordService,
    private translate: TranslateService,
    private toastService: ToastrService,
    public userService: UserService
    ) {}

  publisherNames() {
    const indexName = `name_${this.translate.currentLang}`;
    const publishers = [];
    for (const publisher of this.record.metadata.publishers) {
      let lngName = publisher[indexName];
      if (!lngName) {
        lngName = publisher.name;
      }
      publishers.push(lngName);
    }
    return publishers;
  }

  authorName(author) {
    const indexName = `name_${this.translate.currentLang}`;
    let lngName = author[indexName];
    if (!lngName) {
      lngName = author.name;
    }
    return lngName;
  }

  deleteItem(pid) {
    this.recordsService.delete('items', pid).subscribe((success: any) => {
      if (success) {
        for (const holding of this.record.metadata.holdings) {
          holding.items = holding.items.filter(item => item.pid !== pid);
        }
        this.toastService.success(_('Record deleted'), _('documents'));
      }
    });
  }

  groupItems() {
    const items = [];
    if ('holdings' in this.record.metadata) {
      for (const holding of this.record.metadata.holdings) {
        if ('items' in holding) {
          for (const item of holding.items) {
            items.push(item);
          }
        }
      }
    }
    return items;
  }

  countHoldingsItems() {
    return this.groupItems().length;
  }
}
