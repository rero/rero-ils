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
import { ActivatedRoute } from '@angular/router';
import { RecordsService } from '../../records.service';
import { OrganisationViewService } from '@app/core';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-public-search',
  templateUrl: './public-search.component.html',
  styleUrls: ['./public-search.component.scss']
})
export class PublicSearchComponent implements OnInit {

  viewCode = undefined;
  query = '';
  nDocuments = undefined;
  nPersons = undefined;

  constructor(
    private route: ActivatedRoute,
    private recordsService: RecordsService,
    private organisationView: OrganisationViewService
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
      this.viewCode = results.params.viewcode;
      this.organisationView.setViewCode(results.params.viewcode);
      const query = results.query.get('q');
      if (query) {
        this.query = query;
      }
      this.getCount();
    });
  }

  getCount() {
    this.recordsService.getRecords(this.viewCode, 'documents', 1, 0, this.query).subscribe(results => {
      this.nDocuments = results.hits.total;
    });
    this.recordsService.getRecords(this.viewCode, 'persons', 1, 0, this.query).subscribe(results => {
      this.nPersons = results.hits.total;
    });
  }
}
