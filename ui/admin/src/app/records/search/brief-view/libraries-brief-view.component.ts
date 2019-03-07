import { Component, Input } from '@angular/core';
import { BriefView } from './brief-view';
import { RecordsService } from '../../records.service';

import {AlertsService, _ } from '@app/core';


@Component({
  selector: 'app-libraries-brief-view',
  template: `
  <a class="collapsed card-title text-body"
     data-toggle="collapse" href="#{{'library'+record.metadata.pid }}"
     aria-expanded="false" aria-controls="libraryData">
    <h5 class="mb-0 d-inline">
      <i class="fa fa-caret-down" aria-hidden="true"></i>
      {{record.metadata.name}}
    </h5>
  </a>
  <small> {{record.metadata.code}}</small>
  <section class="card-text">
    <section class="collapse" id="{{'library'+record.metadata.pid }}">
      <dl class="row mb-0">
        <dt class="col-md-2"><span translate>Address</span>:</dt>
        <dd class="col-md-10 mb-0">{{ record.metadata.address }}</dd>
        <dt class="col-md-2"><span translate>Email</span>:</dt>
        <dd class="col-md-10 mb-0"><a href="mailto:{{ record.metadata.email }}">{{ record.metadata.email }}</a></dd>
      </dl>
      <h6 translate class="font-weight-bold mb-0">Opening hours and holidays:</h6>
      <section class="row">
        <ul class="col-lg-6 list-group list-group-flush mb-2">
          <li *ngFor="let opening_hour of record.metadata.opening_hours" class="list-group-item py-0 pr-0 border-0">
            <div *ngIf="opening_hour.is_open" class="row">
              <span class="col-12 col-md-3" translate>{{ opening_hour.day }}:</span>
              <span *ngFor="let time of opening_hour.times"
                    class="col-6 col-md-4 col-lg-3"> {{ time.start_time }} &mdash; {{ time.end_time }}
              </span>
            </div>
            <div *ngIf="!opening_hour.is_open" class="row">
              <span class="col-6 col-md-3">{{ opening_hour.day | translate }}:</span>
              <span class="col-3"> <span translate>Closed</span></span>
            </div>
          </li>
        </ul>
        <ul *ngIf="record.metadata.exception_dates" class="col-lg-6 list-group list-group-flush mb-2">
          <li *ngFor="let exception of record.metadata.exception_dates" class="list-group-item py-0 border-0">
            <div class="row">
              <span class="col-6 col-md-4">
                <i class="fa"
                   [ngClass]="{'fa-check text-success': exception.is_open, 'fa-times text-danger': !exception.is_open }">
                </i> {{ exception.start_date|date:'shortDate' }}
              </span>
              <span class="col-6 col-md-3" *ngIf="exception.end_date"> {{ exception.end_date|date:'shortDate' }}</span>
              <span *ngIf="exception.times">
                <span class="col-6 col-md-4"
                      *ngFor="let time of exception.times"> {{ time.start_time }} &mdash; {{ time.end_time }}
                </span>
              </span>
              <span class="col-12 col-md-4 order-first order-md-last"> {{ exception.title }}</span>
            </div>
          </li>
        </ul>
      </section>
    </section>
    <a class="text-secondary" (click)="toggleCollapse()" [attr.aria-expanded]="!isCollapsed" aria-controls="collapseBasic">
      <i class="fa"
         [ngClass]="{'fa-caret-down': !isCollapsed, 'fa-caret-right': isCollapsed }" aria-hidden="true">
      </i>
      <span translate> locations</span>
    </a>
    <a class="ml-2 text-secondary" routerLinkActive="active"
       [queryParams]="{library: record.metadata.pid}" [routerLink]="['/records/locations/new']">
      <i class="fa fa-plus" aria-hidden="true"></i> {{ 'Add' | translate }}
    </a>
    <div id="collapseBasic" [collapse]="isCollapsed">
      <ul *ngIf="locations.length" class="list-group list-group-flush">
        <li *ngFor="let location of locations;" class="list-group-item p-1">{{ location.metadata.name }}
          <a (click)="deleteLocation(location.metadata.pid)"
          class="float-right text-secondary ml-2" title="{{ 'Delete' | translate }}">
          <i class="fa fa-trash" aria-hidden="true"></i>
          </a>
          <a class="ml-2 float-right text-secondary" routerLinkActive="active"
             [routerLink]="['/records/locations', location.metadata.pid]"
             title="{{ 'Edit' | translate }}">
            <i class="fa fa-pencil" aria-hidden="true"></i>
          </a>
        </li>
      </ul>
      <div *ngIf="!locations.length" translate>{{ 'no location' | translate }}</div>
    </div>
  </section>
  `,
  styles: []
})
export class LibrariesBriefViewComponent implements BriefView {

  @Input() record: any;

  isCollapsed = true;
  locations = [];

  constructor(
    private recordsService: RecordsService,
    private alertsService: AlertsService
  ) {}

  toggleCollapse() {
    if (this.isCollapsed) {
      const libraryPid = this.record.metadata.pid;
      this.recordsService
          .getRecords('locations', 1, 100, `library.pid:${libraryPid}`)
          .subscribe(data => {
            if (data.hits.total) {
              this.locations = data.hits.hits;
            } else {
              this.locations = [];
            }
            this.isCollapsed = !this.isCollapsed;
          });
    } else {
      this.isCollapsed = !this.isCollapsed;
    }
  }

  deleteLocation(pid) {
    this.recordsService.deleteRecord(pid, 'locations').subscribe(success => {
      if (success) {
        this.locations = this.locations.filter(location => location.metadata.pid !== pid);
        this.alertsService.addAlert('warning', _('Record deleted.'));
      }
    });
  }

}
