import { Component, OnInit } from '@angular/core';
import { UserService } from '../../user.service';
import { User } from '../../users';
import { Item, ItemAction, ItemStatus } from '../items';
import { ActivatedRoute, Router } from '@angular/router';
import { ItemsService } from '../items.service';
import { Observable, forkJoin, of } from 'rxjs';
import * as moment from 'moment';
import { TranslateStringService } from '../../translate-string.service';
import { AlertsService } from '@app/core/alerts/alerts.service';
import { DialogService } from '@app/core';

export function _(str: string) {
  return str;
}

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
    return [];
  }

  private confirmConfig: object;


  constructor(
    private userService: UserService,
    private itemsService: ItemsService,
    private route: ActivatedRoute,
    private router: Router,
    private translate: TranslateStringService,
    private alertsService: AlertsService,
    private dialogService: DialogService
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
          this.alertsService.addAlert('info', _('item not found!'));
          return;
        }
      if (item.loan) {
        this.getPatronInfo(item.loan.patron_pid);
      }
      if (item.hasRequests) {
          this.alertsService.addAlert('info', _('The item contains requests'));
      }
      switch (item.actionDone) {
        case ItemAction.return_missing:
          this.alertsService.addAlert('warning', _('the item has been returned from missing'));
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
        this.alertsService.addAlert('info', _('The item is already in the list.'));
      }
    } else {
      this.itemsService.getItem(barcode, this.patron.pid).subscribe(
        (newItem) => {
          if (newItem === null) {
            this.alertsService.addAlert('info', _('item not found!'));
          } else {
            if (newItem.canLoan(this.patron) === false) {
              this.alertsService.addAlert('info', _('item is unavailable!'));
            } else {

              if (newItem.actions === ['no']) {
                this.alertsService.addAlert('info', _('no action possible on this item!'));
              } else {
                newItem.currentAction = ItemAction.checkout;
                this.items.unshift(newItem);
                this.searchText = '';
              }
            }
          }
        },
        (error) => this.alertsService.addAlert('danger', error.message),
        () => console.log('loan success')
      );
    }
  }

  getPatronInfo(patronPID) {
    if (patronPID) {
      this.userService.getUser(patronPID).subscribe(
        (patron) => this.patronInfo = patron,
        (error) => this.alertsService.addAlert('danger', error.message),
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
              this.alertsService.addAlert('info', _('The item is already in the list.'));
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
        (error) => this.alertsService.addAlert('danger', error.message),
        () => console.log('patron success')
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
                this.alertsService.addAlert('info',
                  this.translate.trans(_('The item is ')) + this.translate.trans(newItem.status)
                );
            }
            return newItem;
          }
          return item;
        }).filter(item => item.status === ItemStatus.ON_LOAN);
      },
      (err) => this.alertsService.addAlert('danger', _('an error occurs on the server: ' + err))
    );
  }

  noPendingChange(): Observable<boolean> {
    if (!this.hasPendingActions()) {
      return of(true);
    }
    return this.dialogService.show(this.confirmConfig);
  }

}
