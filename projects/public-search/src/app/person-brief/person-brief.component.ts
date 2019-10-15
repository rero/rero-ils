/*
 * RERO ILS UI
 * Copyright (C) 2019 RERO
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'public-search-person-brief',
  templateUrl: './person-brief.component.html'
})
export class PersonBriefComponent implements OnInit {

  // TODO: adapt following line when issue #23 of ng-core is closed
  private pathArray = window.location.pathname.split('/');

  @Input()
  record: any;

  // TODO: adapt following line when issue #23 of ng-core is closed
  public view = this.pathArray[1];

  constructor() { }

  ngOnInit() {
  }

}
