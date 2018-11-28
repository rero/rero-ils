import { Moment } from 'moment';
import * as moment from 'moment';
import { User } from '../users';

export function _(str) {
  return str;
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

export enum LoanAction {
  checkout = _('checkout'),
  checkin = _('checkin'),
  request = _('request'),
  // lose = _('lose'),
  receive = _('receive'),
  return_missing = _('return_missing'),
  cancel = _('cancel'),
  extend = _('extend'),
  validate = _('validate'),
  no = _('no')
}

export class Item {
  $schema: string;
  available: boolean;
  barcode: string;
  call_number: string;
  document_pid: string;
  item_status: string;
  item_type_name: string;
  item_type_pid: string;
  library_name: string;
  library_pid: string;
  location_name: string;
  location_pid: string;
  pending_loans: string[];
  pid: string;
  requests_count: number;

  constructor(obj?: any) {
    Object.assign(this, obj);
  }
}

export class Loan {

  $schema: string;
  loan_pid: string;
  state: LoanState;

  extension_count?: number;
  transaction_date?: Moment;
  patron_pid?: string;
  document_pid?: string;
  document_title?: string;
  item_pid?: string;
  item_barcode?: string;
  transaction_user_pid?: string;
  transaction_location_pid?: string;
  transaction_location_name?: string;
  transaction_library_pid?: string;
  transaction_library_name?: string;
  pickup_location_pid?: string;
  request_expire_date?: Moment;
  start_date?: Moment;
  end_date?: Moment;
  trigger?: string;
  links?: any;
  request_expired_date?: Moment;
  _currentAction: LoanAction;
  actionDone: LoanAction;
  item: Item;

  constructor(obj?: any) {
    Object.assign(this, obj);
    this.request_expire_date = this.convertToMoment(this.request_expire_date);
    this.start_date = this.convertToMoment(this.start_date);
    this.end_date = this.convertToMoment(this.end_date);
    this.transaction_date = this.convertToMoment(this.transaction_date);
    this.request_expired_date = this.convertToMoment(this.request_expired_date);
  }

  private convertToMoment(data) {
    if (data) {
      return moment(data);
    }
    return undefined;
  }

  public get expired() {
    if (this.dueDate) {
      return this.dueDate.isBefore();
    }
    return false;
  }

  public getActions(patron) {
    if (this.links.actions) {
      return Object.keys(this.links.actions).filter(action => action !== 'cancel');
    }
    return [];
  }

  public set currentAction(action) {
    this._currentAction = action;
  }

  public get currentAction() {
    if (this._currentAction) {
      return this._currentAction;
    }
    return LoanAction.no;
  }

  public isActionLoan() {
    return false;
  }

  public isActionReturn() {
    return false;
  }

  public requestedPosition(patron: User) {
    if (!patron) {
      return 0;
    }
    return this.item.pending_loans.findIndex(
      loan_pid => patron.loans.findIndex(
        loan => loan.loan_pid === loan_pid
      ) >= 0
    ) + 1;
  }

  public get hasRequests() {
    return this.item.pending_loans.length;
  }

  get dueDate() {
    switch (this.state) {
      case LoanState.PENDING:
        return this.request_expired_date;
        break;
      case LoanState.ITEM_ON_LOAN:
        return this.end_date;
        break;
      default:
        return undefined;
        break;
    }
  }
}
