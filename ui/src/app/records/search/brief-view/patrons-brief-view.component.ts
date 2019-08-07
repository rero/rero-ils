/*

RERO ILS
Copyright (C) 2019 RERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

*/

import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';
import { RecordsService } from '../../records.service';

@Component({
  selector: 'app-patrons-brief-view',
  template: `
  <h5 class="card-title mb-0">{{ record.metadata.last_name }}, {{ record.metadata.first_name }}
   <small *ngIf="isPatron()">
      <a [routerLink]="['/circulation', 'checkinout']" [queryParams]="{ patron: record.metadata.barcode}">
        <i class="fa fa-exchange"></i>
        <span translate> Circulation</span>
      </a>
    </small>
  </h5>
  <div class="card-text px-2">
    <p class="mb-0">{{ record.metadata.birth_date | date:'mediumDate' }} &mdash; {{ record.metadata.city }}</p>
    <p class="mb-0">
    <a class="text-secondary" (click)="toggleCollapse()" [attr.aria-expanded]="!isCollapsed">
      <i class="fa"
         [ngClass]="{'fa-caret-down': !isCollapsed, 'fa-caret-right': isCollapsed }" aria-hidden="true">
      </i>
      <span *ngFor="let role of record.metadata.roles; let isLast=last">
        {{ role | translate }}{{isLast ? '' : ', '}}
      </span>
    </a>
    </p>
    <ul [collapse]="isCollapsed" class="list-group list-group-flush" id="{{ 'patron-'+record.metadata.pid }}">
      <li *ngIf="record.metadata.barcode" class="list-group-item p-0 border-0">
        <span translate>Barcode</span>: {{ record.metadata.barcode }}
      </li>
      <li *ngIf="isLibrarian()" class="list-group-item p-0 border-0">
        <span translate>Library</span>: {{ record.metadata.library.name }}
      </li>
      <li *ngIf="isPatron()" class="list-group-item p-0 border-0">
        <span translate>Type</span>: {{ record.metadata.patron_type.name }}
      </li>
      <li *ngIf="record.metadata.phone" class="list-group-item p-0 border-0">
        <span translate>Phone</span>: {{ record.metadata.phone }}
      </li>
      <li class="list-group-item p-0 border-0">
        <span translate>Email</span>: <a href="mailto:{{ record.metadata.email }}">{{ record.metadata.email }}</a>
      </li>
      <li class="list-group-item p-0 border-0">
        <span translate>Street</span>: {{ record.metadata.street }}
      </li>
      <li class="list-group-item p-0 border-0">
        <span translate>City</span>: {{ record.metadata.postal_code }} {{ record.metadata.city }}
      </li>
    </ul>
  </div>
  `,
  styles: []
})
export class PatronsBriefViewComponent implements BriefView {

  @Input() record: any;
  isCollapsed = true;

  constructor(
    private recordsService: RecordsService
  ) {
  }

  isPatron() {
    if (this.record && this.record.metadata.roles) {
      return this.record.metadata.roles.some(role => role === 'patron');
    }
    return false;
  }

  isLibrarian() {
    if (this.record && this.record.metadata.roles) {
      return this.record.metadata.roles.some(role => role === 'librarian');
    }
    return false;
  }

  toggleCollapse() {
    const isCollapsed = this.isCollapsed;
    if (isCollapsed) {
      if (this.isPatron()) {
        const patronTypePid = this.record.metadata.patron_type.pid;
        this.recordsService
          .getRecord('patron_types', patronTypePid, 1)
          .subscribe(data => {
            this.record.metadata.patron_type = data.metadata;
            this.isCollapsed = !isCollapsed;
          });
      }
      if (this.isLibrarian()) {
        const libraryPid = this.record.metadata.library.pid;
        this.recordsService
          .getRecord('libraries', libraryPid, 1)
          .subscribe(data => {
            this.record.metadata.library = data.metadata;
            this.isCollapsed = !isCollapsed;
          });
      }
    } else {
      this.isCollapsed = !isCollapsed;
    }
  }
}
