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

import { Component, EventEmitter, Input, Output } from '@angular/core';
import { User } from '../../users';

@Component({
  selector: 'app-patron-detailed',
  templateUrl: './patron-detailed.component.html',
  styleUrls: ['./patron-detailed.component.scss']
})
export class PatronDetailedComponent {
  @Input() patron: User;
  @Output() clearPatron = new EventEmitter<User>();
  @Input() info: boolean;

  constructor() { }

  clear() {
    if (this.patron) {
      this.clearPatron.emit(this.patron);
    }
  }
}
