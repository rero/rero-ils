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
import { ItemsService } from '../items.service';
import { UserService } from '../../user.service';
import { TranslateStringService } from '../../translate-string.service';
import { ToastrService } from 'ngx-toastr';

export function _(str: string) {
  return str;
}

@Component({
  selector: 'app-main-request',
  templateUrl: './main-request.component.html',
  styleUrls: ['./main-request.component.scss']
})
export class MainRequestComponent implements OnInit {

  public placeholder: string = _('Please enter an item barcode.');
  public searchText = '';
  public items: any[] = null;
  private library_pid: string;

  constructor (
    private userService: UserService,
    private itemsService: ItemsService,
    private translate: TranslateStringService,
    private toastService: ToastrService
  ) {}

  ngOnInit() {
    this.userService.loggedUser.subscribe(user => {
      if (user && user.library.pid) {
        this.library_pid = user.library.pid;
        this.items = null;
        this.getRequestedLoans();
      }
    });
  }

  getRequestedLoans() {
    this.itemsService.getRequestedLoans(this.library_pid).subscribe(items => {
      this.items = items;
    });
  }

  searchValueUpdated(search_text: string) {
    if (! search_text) {
      return null;
    }
    this.searchText = search_text;
    const item = this.items.find(currItem => currItem.barcode === search_text);
    if (item === undefined) {
      this.toastService.warning(
        _('No request corresponding to the given item has been found.'),
        _('search')
      );
    } else {
      const items = this.items;
      this.items = null;
      this.itemsService.doValidateRequest(item).subscribe(
        newItem => {
          this.items = items.map(currItem => {
            if (currItem.pid === newItem.pid) {
              return newItem;
            }
            return currItem;
          });
          this.toastService.warning(
            this.translate.trans(_('The item is ')) + this.translate.trans(newItem.status),
            _('search')
          );
          this.searchText = '';
        }
      );
    }
  }
}
