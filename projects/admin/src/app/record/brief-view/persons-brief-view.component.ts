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
along with this program. If not, see <http://www.gnu.org/licenses/>.

*/

import { Component, Input, OnInit } from '@angular/core';
import { ResultItem } from '@rero/ng-core';

@Component({
  selector: 'admin-persons-brief-view',
  template: `
  <h5 class="card-title mb-0 rero-ils-person">
    <a>{{record.metadata | mefTitle}}</a>
      <small *ngIf="record.metadata.rero" class="badge badge-secondary ml-1">RERO</small>
      <small *ngIf="record.metadata.gnd" class="badge badge-secondary ml-1">GND</small>
      <small *ngIf="record.metadata.bnf" class="badge badge-secondary ml-1">BNF</small>
  </h5>
  <div class="card-text px-2">
    <p class="mb-0" *ngIf="record.metadata | birthDate">{{ record.metadata | birthDate }}</p>
    <p class="mb-0" *ngIf="record.metadata | bioInformations">{{ record.metadata | bioInformations }}</p>
  </div>
  `,
  styles: []
})
export class PersonsBriefViewComponent implements ResultItem {

  @Input()
  record: any;

  @Input()
  type: string;

}
