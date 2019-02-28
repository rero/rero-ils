import { Component, OnInit } from '@angular/core';
import { RecordsService } from '../records.service';
import { AlertsService, _ } from '@app/core';
import { ActivatedRoute, Router } from '@angular/router';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';


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
  public aggregations = null;
  public aggFilters = [];
  public searchMime = 'application/json';

  constructor(
    private recordsService: RecordsService,
    private route: ActivatedRoute,
    private router: Router,
    private alertsService: AlertsService
    ) {}

  ngOnInit() {
    combineLatest(this.route.params, this.route.queryParamMap)
    .pipe(map(results => ({params: results[0], query: results[1]})))
    .subscribe(results => {
      const params = results.params;
      const query = results.query;
      // parse url
      this.aggFilters = [];
      this.recordType = params.recordType;
      if (this.recordType === 'documents') {
        this.searchMime = 'application/rero+json';
      }
      for (const key of query.keys) {
        switch (key) {
          case 'q': {
            this.query = query.get(key);
            break;
          }
          case 'size': {
            this.nPerPage = +query.get(key);
            break;
          }
          case 'page': {
            this.currentPage = +query.get(key);
            break;
          }
          default: {
            for (const value of query.getAll(key)) {
              const filterValue = `${key}=${value}`;
              this.aggFilters.push(filterValue);
            }
            break;
          }
        }
      }

      this.placeholder = 'Search for' + ` ${this.recordType}`;
      this.getRecords();
    });
  }

  getRecords() {
    this.recordsService.getRecords(
      this.recordType,
      this.currentPage,
      this.nPerPage,
      this.query,
      this.searchMime,
      this.aggFilters
    ).subscribe(data => {
      if (data === null) {
        this.notFound = true;
        this.alertsService.addAlert('info', _('No result found.'));
      } else {
        this.records = data.hits.hits;
        this.aggregations = data.aggregations;
        this.total = data.hits.total;
        if (this.records.length === 0 && this.currentPage > 1) {
          this.currentPage -= 1;
          this.updateRoute();
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

  updateRoute() {
    const queryParams = {
      size: this.nPerPage,
      page: this.currentPage,
      q: this.query
    };
    const filters = {};
    for (const filter of this.aggFilters) {
      const [key, value] = filter.split('=');
      if (!filters[key]) {
        filters[key] = [];
      }
      filters[key].push(value);
    }
    Object.keys(filters).map(key => queryParams[key] = filters[key]);
    this.router.navigate([], { queryParams : queryParams });
  }

  pageChanged(event: any): void {
    this.currentPage = event.page;
    this.nPerPage = event.itemsPerPage;
    this.updateRoute();
  }

  searchValueUpdated(searchValue: string) {
    this.query = searchValue;
    this.updateRoute();
  }

  deleteRecord(pid) {
    this.recordsService.deleteRecord(pid, this.recordType).subscribe(success => {
      if (success) {
        this.alertsService.addAlert('warning', _('Record deleted.'));
        this.getRecords();
      }
    });
  }

  aggFilter(term, value) {
    const filterValue = `${term}=${value}`;
    if (this.isFiltered(term, value)) {
      this.aggFilters = this.aggFilters.filter(val => val !== filterValue);
    } else {
      this.aggFilters.push(filterValue);
    }
    this.updateRoute();
  }

  isFiltered(term, value) {
    const filterValue = `${term}=${value}`;
    return this.aggFilters.some(val => filterValue === val);
  }
}
