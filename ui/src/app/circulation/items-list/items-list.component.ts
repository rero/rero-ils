import { Component, Input, Output, EventEmitter } from '@angular/core';
import { ItemAction } from '../items';
import { User } from '../../users';

@Component({
  selector: 'app-items-list',
  templateUrl: './items-list.component.html',
  styleUrls: ['./items-list.component.scss']
})
export class ItemsListComponent {

  @Input() items: any[];
  @Input() patron: User;
  @Output() applyItems = new EventEmitter<any[]>();

  constructor() {
    this.items =  null;
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
