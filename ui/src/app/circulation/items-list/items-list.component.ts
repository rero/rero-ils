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

import { Component, Input, Output, EventEmitter } from '@angular/core';
import { ItemAction } from '../items';
import { User } from '../../users';
import { OrganisationViewService } from '@app/core';

@Component({
  selector: 'app-items-list',
  templateUrl: './items-list.component.html',
  styleUrls: ['./items-list.component.scss']
})
export class ItemsListComponent {

  @Input() items: any[];
  @Input() patron: User;
  @Output() applyItems = new EventEmitter<any[]>();

  viewcode = undefined;

  constructor(
    organisationViewService: OrganisationViewService
  ) {
    this.items =  null;
    this.viewcode = organisationViewService.getViewCode();
  }

  apply(items: any[]) {
     if (items.length) {
      this.applyItems.emit(items);
    }
  }

  warningRequests(item) {
    if (this.patron) {
      return item.hasRequests
          && (item.currentAction === ItemAction.checkin);
    } else {
      return item.hasRequests;
    }
  }

  hasPendingActions() {
    if (this.patron) {
      if (this.items.filter(item => item.currentAction !== ItemAction.no).length > 0) {
        return true;
      }
    }
    return false;
  }
}
