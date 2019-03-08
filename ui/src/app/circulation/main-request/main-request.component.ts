import { Component, OnInit } from '@angular/core';
import { ItemsService } from '../items.service';
import { UserService } from '../../user.service';
import { AlertComponent } from 'ngx-bootstrap/alert/alert.component';
import { TranslateStringService } from '../../translate-string.service';
import { AlertsService } from '@app/core/alerts/alerts.service';

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
    private alertsService: AlertsService

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
      this.alertsService.addAlert('warning', _('No request corresponding to the given item has been found.'));
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
          this.alertsService.addAlert('warning', this.translate.trans(_('The item is ')) + this.translate.trans(newItem.status));
          this.searchText = '';
        }
      );
    }
  }
}
