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

import { Component, OnInit, Input } from '@angular/core';
import { RecordsService } from '../records.service';
import { _, OrganisationViewService } from '@app/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslateService } from '@ngx-translate/core';
import { ToastrService } from 'ngx-toastr';


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
  set displayScore(value) {
    if (value !== undefined) {
      this._displayScore = value;
      this.getRecords();
    }
  }
  get displayScore() {
    return this._displayScore;
  }
  private _displayScore = 0;

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
  set sort(value) {
    if (value !== undefined) {
      this._sort = value;
      this.getRecords();
    }
  }
  get sort() {
    return this._sort;
  }
  private _sort = undefined;

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
  public language = null;
  public permissions = null;
  onInitDone = false;

  constructor(
    protected recordsService: RecordsService,
    protected route: ActivatedRoute,
    protected router: Router,
    private translate: TranslateService,
    private toastService: ToastrService,
    private organisationView: OrganisationViewService
   ) {}

  ngOnInit() {
    this.onInitDone = true;
    this.language = this.translate.currentLang;
    if (this.recordType === 'documents') {
      this.searchMime = 'application/rero+json';
    }
    this.placeholder = this.translate.instant(_('Search for')) + ' ' + this.translate.instant(this.recordType);
    this.getRecords();
  }


  getRecords() {
    if (!this.onInitDone) {
      return;
    }
    // add sort options only for a non query request
    let sort;
    if (!this.query) {
      sort = this.sort;
    }
    this.recordsService.getRecords(
      this.organisationView.getViewCode(),
      this.recordType,
      this.currentPage,
      this.nPerPage,
      this.query,
      this.searchMime,
      this.aggFilters,
      sort,
      this.displayScore
    ).subscribe(data => {
      if (data === null) {
        this.notFound = true;
      } else {
        this.records = data.hits.hits;
        this.permissions = null;
        if (data.permissions) {
          this.permissions = data.permissions;
        }
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
          if (agg in data.aggregations) {
            const agg_value  = data.aggregations[agg];
            agg_value.title = agg;
            agg_value.name = agg;
            const agg_split = agg.split('__');
            if (agg_split.length === 2) {
              if (this.language === agg_split[1]) {
                agg_value.name = agg_split[0];
                this.aggregations.push(agg_value);
              }
            } else {
              this.aggregations.push(agg_value);
            }
          }
        }

        this.total = data.hits.total;
        if (this.records.length === 0 && this.currentPage > 1) {
          this.currentPage -= 1;
          this.updateRoute();
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
    if (this.displayScore) {
      queryParams['display_score'] = this.displayScore;
    }
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
        this.toastService.success('Record deleted.', this.recordType);
        this.getRecords();
      }
    });
  }

  hasPermissionToCreate() {
    if (this.permissions
        && this.permissions.cannot_create
        && this.permissions.cannot_create.permission) {
      return false;
    }
    return true;
  }

  removeAggFilter(event: any) {
    this.aggFilters = this.aggFilters.filter(
      val => val !== this.formatFilterValue(event)
    );
    this.updateRoute();
  }

  addAggFilter(event: any) {
    this.aggFilters.push(this.formatFilterValue(event));
    this.updateRoute();
  }

  formatFilterValue(object: {term: string, value: string}) {
    return `${object.term}=${object.value}`;
  }
}
