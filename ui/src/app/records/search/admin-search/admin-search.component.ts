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

import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-admin-search',
  templateUrl: './admin-search.component.html',
  styleUrls: ['./admin-search.component.scss']
})
export class AdminSearchComponent implements OnInit {
  public recordType = undefined;
  public query = '';
  public nPerPage = 10;
  public currentPage = 1;
  public aggFilters = [];

  constructor(
    protected route: ActivatedRoute,
    protected router: Router
  ) { }

  ngOnInit() {
    combineLatest(this.route.params, this.route.queryParamMap)
    .pipe(map(results => ({params: results[0], query: results[1]})))
    .subscribe(results => {
      const params = results.params;
      const urlQuery = results.query;
      this.recordType = params.recordType;
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
