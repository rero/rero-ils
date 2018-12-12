import { Component, OnInit } from '@angular/core';
import { RecordsService } from '../records.service';
import { ActivatedRoute } from '@angular/router';
import { AlertsService } from '@app/core/alerts/alerts.service';

export function _(str: string) {
  return str;
}

@Component({
  selector: 'app-search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.scss']
})
export class SearchComponent implements OnInit {

  public records: Object[] = [];
  public total = 0;
  public nPerPage = 10;
  public currentPage = 1;
  public recordType = undefined;
  public query = '';
  public placeholder = '';
  public notFound = false;

  constructor(
    private recordsService: RecordsService,
    private route: ActivatedRoute,
    private alertsService: AlertsService
  ) {}

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.recordType = params.recordType;
      this.placeholder = `search in ${this.recordType}`;
      this.getRecords();
    });
  }

  getRecords() {
    this.recordsService.getRecords(
      this.recordType,
      this.currentPage,
      this.nPerPage,
      this.query
    ).subscribe(data => {
        if (data === null) {
          this.notFound = true;
          this.alertsService.addAlert('info', _('No result found.'));
        } else {
          this.records = data.hits.hits;
          this.total = data.hits.total;
          if (this.records.length === 0 && this.currentPage > 1) {
            this.currentPage -= 1;
            this.getRecords();
          }
          if (data.hits.total === 0) {
            this.alertsService.addAlert('info', _('No result found.'));
          }
        }
      });
    }
    showPagination() {
      if (this.total > this.nPerPage) {
        return true;
      }
      return false;
    }

    pageChanged(event: any): void {
      this.currentPage = event.page;
      this.nPerPage = event.itemsPerPage;
      this.getRecords();
    }

    searchValueUpdated(searchValue: string) {
      this.query = searchValue;
      this.getRecords();
    }

    deleteRecord(pid) {
      this.recordsService.delete(this.recordType, pid).subscribe(record => {
        this.alertsService.addAlert('warning', _('Record deleted.'));
        this.getRecords();
      });
    }
  }
