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

@Component({
  selector: 'app-public-search',
  templateUrl: './public-search.component.html',
  styleUrls: ['./public-search.component.scss']
})
export class PublicSearchComponent implements OnInit {
  query = '';
  nDocuments = undefined;
  nPersons = undefined;
  constructor(
    private route: ActivatedRoute,
    private recordsService: RecordsService
  ) { }

  ngOnInit() {
    this.route.queryParamMap.subscribe((params: any) => {
      const query = params.get('q');
      if (query) {
        this.query = query;
      }
      this.getCount();
    });
  }

  getCount() {
    this.recordsService.getRecords('documents', 1, 0, this.query).subscribe(results => {
      this.nDocuments = results.hits.total;
    });
    this.recordsService.getRecords('persons', 1, 0, this.query).subscribe(results => {
      this.nPersons = results.hits.total;
    });
  }

}
