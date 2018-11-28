import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';
import { Loan, LoanAction } from '../loans';
import { User } from '../../users';

@Component({
  selector: 'app-loans-list',
  templateUrl: './loans-list.component.html',
  styleUrls: ['./loans-list.component.scss']
})
export class LoansListComponent implements OnInit {

  @Input() loans: Loan[];
  @Input() patron: User;
  @Output() removeLoan = new EventEmitter<Loan>();
  @Output() applyLoans = new EventEmitter<Loan[]>();

  constructor() {
    this.loans =  null;
  }

  ngOnInit() {
  }

  remove(loan: Loan) {
    if (loan) {
      this.removeLoan.emit(loan);
    }
  }

  apply(loans: Loan[]) {
     if (loans.length) {
      this.applyLoans.emit(loans);
    }
  }

  warningRequests(loan) {
    if (this.patron) {
      return loan.hasRequests
          && (loan.currentAction === LoanAction.checkin);
    } else {
      return loan.hasRequests;
    }
  }

  // TODO: move to a LoansList class
  hasPendingActions() {
    if (this.patron) {
      if (this.loans.filter(loan => loan.currentAction !== LoanAction.no).length > 0) {
        return true;
      }
    }
    return false;
  }
}
