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
import { UserService } from '../../user.service';
import { User } from '../../users';
import { Item, ItemAction, ItemStatus } from '../items';
import { ActivatedRoute, Router } from '@angular/router';
import { ItemsService } from '../items.service';
import { Observable, forkJoin, of } from 'rxjs';
import { TranslateStringService } from '../../translate-string.service';
import { DialogService } from '@app/core';
import { _ } from '@app/core';
import { ToastrService } from 'ngx-toastr';


export interface NoPendingChange {
    noPendingChange(): boolean | Observable<boolean>;
}

@Component({
  selector: 'app-main-checkin-checkout',
  templateUrl: './main-checkin-checkout.component.html',
  styleUrls: ['./main-checkin-checkout.component.scss']
})
export class MainCheckinCheckoutComponent implements OnInit, NoPendingChange {

  public placeholder: string = _('Please enter a patron card number or an item barcode.');
  public searchText = '';
  private library_pid: string;
  public patron: User;
  public patronInfo: User;

  private loggedUser: User;
  private _items = [];

  public get items() {
    if (this.patron) {
      return this.patron.items;
    } else {
      return this._items;
    }
  }

  private confirmConfig: object;


  constructor(
    private userService: UserService,
    private itemsService: ItemsService,
    private route: ActivatedRoute,
    private router: Router,
    private translate: TranslateStringService,
    private dialogService: DialogService,
    private toastService: ToastrService
    ) {
    route.queryParamMap.subscribe(
      params => {
        const barcode = params.get('patron');
        if (!this.patron || (barcode !== this.patron.barcode)) {
          this.getPatronOrItem(barcode);
        }
      }
    );
    this.confirmConfig = {
      ignoreBackdropClick: true,
      initialState: {
        title: this.translate.trans(_('Confirmation')),
        body: this.translate.trans(_('Exit without saving changes?')),
        confirmButton: true,
        confirmTitleButton: _('OK'),
        cancelTitleButton: _('Cancel')
      }
    };
  }

  ngOnInit() {
    this.userService.loggedUser.subscribe(user => {
      this.loggedUser = user;
    });
  }

  searchValueUpdated(searchText: string) {
    if (!searchText) {
      return null;
    }
    this.searchText = searchText;
    if (this.patron) {
      this.getItem(searchText);
    } else {
      this.getPatronOrItem(searchText);
    }
  }

  automaticCheckinCheckout(item_barcode) {
    this.itemsService.automaticCheckin(item_barcode).subscribe(item => {
      // TODO: remove this when policy will be in place
      if (item === null) {
        this.toastService.warning(_('item not found!'), _('checkin'));
        return;
        }
      if (item.loan) {
        this.getPatronInfo(item.loan.patron_pid);
      }
      if (item.hasRequests) {
        this.toastService.warning(_('The item contains requests'), _('checkin'));
      }
      switch (item.actionDone) {
        case ItemAction.return_missing:
          this.toastService.warning(
            _('the item has been returned from missing'),
            _('checkin')
          );
          break;
        default:
          break;
      }
      this._items.unshift(item);
      this.searchText = '';
    });
  }

  getItem(barcode: string) {
    const item = this.items.find(currItem => currItem.barcode === barcode);
    if (item) {
      if (this.patron) {
        item.currentAction = ItemAction.checkin;
        this.searchText = '';
      } else {
        this.toastService.warning(_('The item is already in the list.'), _('checkin'));
      }
    } else {
      this.itemsService.getItem(barcode, this.patron.pid).subscribe(
        (newItem) => {
          if (newItem === null) {
            this.toastService.warning(_('item not found!'), _('checkin'));
          } else {
            if (newItem.canLoan(this.patron) === false) {
              this.toastService.warning(_('item is unavailable!'), _('checkin'));
            } else {
              if (newItem.actions.length === 1 && newItem.actions.indexOf('no') > -1) {
                this.toastService.warning(_('no action possible on this item!'), _('checkin'));
              } else {
                newItem.currentAction = ItemAction.checkout;
                this.items.unshift(newItem);
                this.searchText = '';
              }
            }
          }
        },
        (error) => this.toastService.error(
          error.message,
          _('checkin')
        ), () => console.log('loan success')
      );
    }
  }

  getPatronInfo(patronPID) {
    if (patronPID) {
      this.userService.getUser(patronPID).subscribe(
        (patron) => this.patronInfo = patron,
        (error) => this.toastService.error(
          error.message,
          _('checkin')
        ),
        () => console.log('patron by pid success')
      );
    } else {
      this.patronInfo = null;
    }
  }

  getPatronOrItem(barcode: string) {
    if (barcode) {
      this.userService.getPatron(barcode).subscribe(
        (patron) => {
          if (patron === null) {
            const newItem = this.items.find(item => item.barcode === barcode);
            if (newItem) {
              this.toastService.warning(_('The item is already in the list.'), _('checkin'));
            } else {
              this.automaticCheckinCheckout(barcode);
            }
          } else {
            let loanableItems = [];
            if (this._items.length) {
              loanableItems = this._items.filter(item => item.canLoan(patron));
            }
            this.patronInfo = null;
            this.patron = patron;
            if (loanableItems.length) {
              const item = loanableItems[0];
              item.currentAction = ItemAction.checkout;
              item.actionDone = undefined;
              this.patron.items.unshift(item);
            }
            this.router.navigate([], { queryParams: {
              patron: this.patron.barcode
            }});
            this.searchText = '';
          }
        },
        (error) => this.toastService.error(
          error.message,
          _('checkin')
        ), () => console.log('patron success')
      );
    }
  }

  clearPatron(patron: User) {
    if (this.hasPendingActions()) {

      this.dialogService.show(this.confirmConfig).subscribe((confirm: boolean) => {
          if (confirm) {
           this.doClearPatron();
          }
      });
    } else {
      this.doClearPatron();
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

  doClearPatron() {
    this.patron = null;
    this.placeholder = _('Please enter a patron card number or an item barcode.');
    this.searchText = '';
    this._items = [];
    this.router.navigate([], { queryParams: {}});
  }

  applyItems(items: Item[]) {
    const observables = [];
    for (const item of items) {
      if (item.currentAction !== ItemAction.no) {
        observables.push(this.itemsService.doAction(item, this.patron.pid));
      }
    }
    forkJoin(observables).subscribe(
      (newItems) => {
        this.patron.items = this.patron.items.map(item => {
          const newItem = newItems.filter(currItem => currItem.pid === item.pid).pop();
          if (newItem) {
            if (newItem.status === ItemStatus.IN_TRANSIT) {
              this.toastService.success(
                this.translate.trans(_('The item is ')) + this.translate.trans(newItem.status),
                _('checkin')
              );
            } else {
              if (newItem.status === ItemStatus.AT_DESK) {
                this.toastService.success(
                  this.translate.trans(_('The item is ')) + this.translate.trans(newItem.status),
                  _('checkin')
                );
              }
            }
            return newItem;
          }
          return item;
        }).filter(item => item.status === ItemStatus.ON_LOAN);
      },
      (err) => this.toastService.error(
        _('an error occurs on the server: ') + err,
        _('checkin')
      )
    );
  }

  noPendingChange(): Observable<boolean> {
    if (!this.hasPendingActions()) {
      return of(true);
    }
    return this.dialogService.show(this.confirmConfig);
  }

}
