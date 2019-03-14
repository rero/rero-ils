import { Component, OnInit, Input } from '@angular/core';
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

  @Input()
  set adminMode(value) {
    if (value !== undefined) {
      this._adminMode = value;
      this.getRecords();
    }
  }
  get adminMode() {
    return this._adminMode;
  }
  private _adminMode = undefined;

  @Input()
  set recordType(value) {
    if (value !== undefined) {
      this._recordType = value;
      this.getRecords();
    }
  }
  get recordType() {
    return this._recordType;
  }
  private _recordType = undefined;

  @Input()
  set query(value) {
    if (value !== undefined) {
      this._query = value;
      this.getRecords();
    }
  }
  get query() {
    return this._query;
  }
  private _query = '';

  @Input()
  set nPerPage(value) {
    if (value !== undefined) {
      this._nPerPage = value;
      this.getRecords();
    }
  }
  get nPerPage() {
    return this._nPerPage;
  }
  private _nPerPage = 10;

  @Input()
  set currentPage(value) {
    if (value !== undefined) {
      this._currentPage = value;
      this.getRecords();
    }
  }
  get currentPage() {
    return this._currentPage;
  }
  private _currentPage = 1;

  @Input()
  set aggFilters(value) {
    if (value !== undefined) {
      this._aggFilters = value;
      this.getRecords();
    }
  }
  get aggFilters() {
    return this._aggFilters;
  }
  private _aggFilters = [];

  @Input()
  set showSearchInput(value) {
    if (value !== undefined) {
      this._showSearchInput = value;
      this.getRecords();
    }
  }
  get showSearchInput() {
    return this._showSearchInput;
  }
  private _showSearchInput = false;

  get briefViewName() {
    if (this._adminMode) {
      return this._recordType;
    }
    return `public_${this._recordType}`;
  }
  public records: Object[] = [];
  public total = 0;
  public placeholder = '';
  public notFound = false;
  public aggregations = null;
  public aggsSettings = null;
  public searchMime = 'application/json';
  onInitDone = false;
  constructor(
    protected recordsService: RecordsService,
    protected route: ActivatedRoute,
    protected router: Router,
    protected alertsService: AlertsService
   ) {}

  ngOnInit() {
    this.onInitDone = true;
    if (this.recordType === 'documents') {
      this.searchMime = 'application/rero+json';
    }
    this.placeholder = 'Search for' + ` ${this.recordType}`;
    this.getRecords();
  }


  getRecords() {
    if (!this.onInitDone) {
      return;
    }
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

        this.aggregations = [];
        this.aggsSettings = data.aggregations._settings;
        if (this.aggsSettings !== undefined) {
          delete data.aggregations._settings;
        }
        let order = [];
        if (this.aggsSettings) {
          order = this.aggsSettings.order;
        }
        if (!order) {
          order = Object.keys(data.aggregations);
        }
        for (const agg of order) {
          const agg_value  = data.aggregations[agg];
          agg_value.title = agg;
          this.aggregations.push(agg_value);
        }

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

  isFiltered(term, value?) {
    if (value) {
      const filterValue = `${term}=${value}`;
      return this.aggFilters.some(val => filterValue === val);
    } else {
      return this.aggFilters.some(val => term === val.split('=')[0]);
    }
  }

  startOpen(title: string) {
    if (this.isFiltered(title)) {
      return true;
    }
    if (this.aggsSettings.expand.some(value => value === title)) {
      return true;
    }
    return false;
  }
  // isCollapsed(title) {
  //   return this.startOpen(title);
  // }
  // toggleCollapsed(title) {
  //   return;
  // }
}
