import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';

@Component({
  selector: 'app-patrons-brief-view',
  template: `
  <h5 class="card-title mb-0">{{ record.metadata.last_name }}, {{ record.metadata.first_name }}
   <small *ngIf="isPatron()">
      <a href="/admin/circulation/checkinout?patron={{ record.metadata.barcode }}">
        <i class="fa fa-exchange"></i>
        <span translate>Circulation</span>
      </a>
    </small>
  </h5>
  <div class="card-text px-2">
    <p class="mb-0">{{ record.metadata.birth_date }} &mdash; {{ record.metadata.city }}</p>
    <p class="mb-0">{{ record.metadata.roles }}
    <a class="collapsed text-secondary"
       data-toggle="collapse"
       href="#{{ 'patron-'+record.metadata.pid }}"
       aria-expanded="false"
       aria-controls="patronDetailed"
    >
        <i class="fa fa-caret-down" aria-hidden="true"></i>
    </a>
    </p>
    <ul class="collapse list-group list-group-flush" id="{{ 'patron-'+record.metadata.pid }}">
      <li *ngIf="record.metadata.barcode" class="list-group-item p-0 border-0">
        <span translate>Barcode</span>: {{ record.metadata.barcode }}
      </li>
      <li *ngIf="isPatron()" class="list-group-item p-0 border-0">
        <span translate>Type</span>: {{ record.metadata.patron_type.pid }}
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
}
