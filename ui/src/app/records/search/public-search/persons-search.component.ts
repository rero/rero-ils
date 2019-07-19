import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-persons-search',
  template: `
    <app-search
      [aggFilters]="aggFilters"
      [query]="query"
      [recordType]="recordType"
      [nPerPage]="nPerPage"
      [currentPage]="currentPage"
      [aggFilters]="aggFilters"
      [showSearchInput]="false"
    >
    </app-search>
  `,
  styles: []
})
export class PersonsSearchComponent implements OnInit {
  public viewCode = undefined;
  public recordType = 'persons';
  public query = '';
  public nPerPage = 10;
  public currentPage = 1;
  public aggFilters = [];
  public test;

  constructor(
    protected route: ActivatedRoute,
    protected router: Router
  ) { }

  ngOnInit() {
    combineLatest(
      this.route.params,
      this.route.queryParamMap
    ).pipe(map(results => ({
      params: results[0],
      query: results[1]
    })))
    .subscribe(results => {
      const urlQuery = results.query;
      this.aggFilters = [];
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
          default: {
            for (const value of urlQuery.getAll(key)) {
              const filterValue = `${key}=${value}`;
              this.aggFilters.push(filterValue);
            }
            break;
          }
        }
      }
    });
  }
}
