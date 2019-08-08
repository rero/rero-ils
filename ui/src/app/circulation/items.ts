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

import { Moment } from 'moment';
import * as moment from 'moment';
import { User } from '../users';

export function _(str) {
  return str;
}

export enum ItemStatus {
  ON_SHELF = _('on_shelf'),
  AT_DESK = _('at_desk'),
  ON_LOAN = _('on_loan'),
  IN_TRANSIT = _('in_transit'),
  EXCLUDED = _('excluded'),
  MISSING = _('missing')
}

export enum LoanState {
  CREATED = _('CREATED'),
  PENDING = _('PENDING'),
  ITEM_ON_LOAN = _('ITEM_ON_LOAN'),
  ITEM_RETURNED = _('ITEM_RETURNED'),
  ITEM_IN_TRANSIT_FOR_PICKUP = _('ITEM_IN_TRANSIT_FOR_PICKUP'),
  ITEM_IN_TRANSIT_TO_HOUSE = _('ITEM_IN_TRANSIT_TO_HOUSE'),
  ITEM_AT_DESK = _('ITEM_AT_DESK'),
  CANCELLED = _('CANCELLED')
}

export interface Document {
  pid: string;
  title: string;
}

export enum ItemAction {
  checkout = _('checkout'),
  checkin = _('checkin'),
  request = _('request'),
  lose = _('lose'),
  receive = _('receive'),
  return_missing = _('return_missing'),
  // cancel_loan = _('cancel_loan'),
  extend_loan = _('extend_loan'),
  validate_request = _('validate_request'),
  no = _('no')
}

type ItemActionObjectType<R> = {[key in keyof typeof ItemAction]: R };

export class Loan {

  pid?: string;
  state: LoanState;
  transaction_date?: Moment;
  patron_pid?: string;
  item_pid?: string;
  start_date?: Moment;
  end_date?: Moment;
  request_expire_date?: Moment;
  constructor(obj?: any) {
    Object.assign(this, obj);
    this.request_expire_date = this.convertToMoment(this.request_expire_date);
    this.start_date = this.convertToMoment(this.start_date);
    this.end_date = this.convertToMoment(this.end_date);
    this.transaction_date = this.convertToMoment(this.transaction_date);
  }

  private convertToMoment(data) {
    if (data) {
      return moment(data);
    }
    return undefined;
  }

  get dueDate() {
    switch (this.state) {
      case LoanState.PENDING:
      return this.request_expire_date;
      break;
      case LoanState.ITEM_ON_LOAN:
      return this.end_date;
      break;
      default:
      return undefined;
      break;
    }
  }

  public get expired() {
    if (this.dueDate) {
      return this.dueDate.isBefore();
    }
    return false;
  }
}
export class Item {
  available: boolean;
  barcode: string;
  call_number: string;
  document: string;
  status: ItemStatus;
  pid: string;
  requests_count: number;
  action_applied?: ItemActionObjectType<object>;
  _currentAction: ItemAction;
  actionDone: ItemAction;
  loan: Loan;
  actions: ItemAction[];
  pending_loans: Loan[];
  number_of_extensions: number;

  constructor(obj?: any) {
    Object.assign(this, obj);
    if (obj.pending_loans) {
      this.pending_loans = obj.pending_loans.map(loan => new Loan(loan));
    }
    this.actions.unshift(ItemAction.no);
  }

  setLoan(obj?: any) {
    this.loan = new Loan(obj);
  }

  public set currentAction(action: ItemAction) {
    // if(this.actions.some(
    //     (a: ItemAction) => a === action)
    // ) {
      this._currentAction = action;
      // }
    }
    public get currentAction() {
      if (this._currentAction) {
        return this._currentAction;
      }
      return ItemAction.no;
    }
    // should rely on backend and delete this function
    public canLoan(patron) {
      if (!this.available) {
        if ((this.status === ItemStatus.AT_DESK || this.status === ItemStatus.IN_TRANSIT)
            && patron
            && this.pending_loans
            && this.pending_loans.length
            && this.pending_loans[0].patron_pid === patron.pid) {
          return true;
      }
      return true;
    }
    // available
    return true;
  }

  public isActionLoan() {
    return this.currentAction === ItemAction.checkout;
  }

  public isActionReturn() {
    return this.currentAction === ItemAction.checkin;
  }

  public requestedPosition(patron: User) {
    if (!patron || !this.pending_loans) {
      return 0;
    }
    return this.pending_loans.findIndex(
      loan => loan.patron_pid === patron.pid
      ) + 1;
  }

  public get hasRequests() {
    if (!this.pending_loans) {
      return false;
    }
    return this.pending_loans.length;
  }
}

