import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';
import { OrganisationViewService } from '@app/core';

@Component({
  selector: 'app-documents-search',
  template: `
    <app-search
      [aggFilters]="aggFilters"
      [query]="query"
      [recordType]="recordType"
      [nPerPage]="nPerPage"
      [currentPage]="currentPage"
      [aggFilters]="aggFilters"
      [showSearchInput]="false"
      [displayScore]="displayScore"
    >
    </app-search>
  `,
  styles: []
})
export class DocumentsSearchComponent implements OnInit {
  public recordType = 'documents';
  public query = undefined;
  public nPerPage = undefined;
  public currentPage = undefined;
  public aggFilters = undefined;
  public displayScore = undefined;

  constructor(
    protected route: ActivatedRoute,
    protected router: Router
  ) { }

  ngOnInit() {
    combineLatest(this.route.params, this.route.queryParamMap)
    .pipe(map(results => ({params: results[0], query: results[1]})))
    .subscribe(results => {
      const urlQuery = results.query;
      const aggFilters = [];
      // parse url
      for (const key of urlQuery.keys) {
        switch (key) {
          case 'q': {
            this.query = urlQuery.get(key);
            break;
          }
          case 'size': {
            this.nPerPage = +urlQuery.get(key);
            break;
          }
          case 'page': {
            this.currentPage = +urlQuery.get(key);
            break;
          }
          case 'display_score': {
            this.displayScore = +urlQuery.get(key);
            break;
          }
          default: {
            for (const value of urlQuery.getAll(key)) {
              const filterValue = `${key}=${value}`;
              aggFilters.push(filterValue);
            }
            break;
          }
        }
      }
      this.aggFilters = aggFilters;
    });
  }
}
