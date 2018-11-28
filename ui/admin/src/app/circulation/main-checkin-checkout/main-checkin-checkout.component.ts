import { Component, OnInit } from '@angular/core';
import { UserService } from '../../user.service';
import { User } from '../../users';
import { Loan, LoanAction } from '../loans';
import { ActivatedRoute, Router } from '@angular/router';
import { AlertComponent } from 'ngx-bootstrap/alert/alert.component';
import { LoansService } from '../loans.service';
import { Observable, forkJoin } from 'rxjs';

export function _(str: string) {
  return str;
}

@Component({
  selector: 'app-main-checkin-checkout',
  templateUrl: './main-checkin-checkout.component.html',
  styleUrls: ['./main-checkin-checkout.component.scss']
})
export class MainCheckinCheckoutComponent implements OnInit {

  public placeholder: string = _('Please enter a patron card number or an item barcode.');
  public searchText = '';
  private library_pid: string;
  public alerts: any[] = [];
  public patron: User;
  public confirm_changes = false;
  private alertTimeout = 5000;

  public get loans() {
    if (this.patron) {
      return this.patron.loans;
    }
    return [];
  }
  constructor(
    private userService: UserService,
    private loansService: LoansService,
    private route: ActivatedRoute,
    private router: Router
    ) {
    route.queryParamMap.subscribe(
      params => this.getPatron(params.get('patron'))
    );
  }

  ngOnInit() {
  }

  searchValueUpdated(search_text: string) {
    this.getPatron(search_text);
  }

  onAlertClosed(dismissedAlert: AlertComponent): void {
    this.alerts = this.alerts.filter(alert => alert !== dismissedAlert);
  }

  getPatron(barcode: string) {
    if (barcode) {
      this.userService.getPatron(barcode).subscribe(
        (patron) => {
          if (patron === null) {
            this.addAlert('info', _('patron not found!'));
          } else {
            this.patron = patron;
            this.router.navigate([], { queryParams: {
              patron: this.patron.barcode
            }});
          }
        },
        (error) => this.addAlert('danger', error.message),
        () => console.log('success')
      );
    }
  }

  clearPatron(patron: User) {
    if (this.hasPendingActions()) {
      this.confirm_changes = true;
    } else {
      this.doClearPatron();
    }
  }

  confirmRemovePatron(ok: boolean) {
    if (ok === true) {
      this.doClearPatron();
    } else {
      console.log('ko');
      this.confirm_changes = false;
    }

  }
  hasPendingActions() {
    if (this.patron) {
      if (this.loans.filter(loan => loan.currentAction !== LoanAction.no).length > 0) {
        return true;
      }
    }
    return false;
  }

  doClearPatron() {
    this.patron = null;
    this.placeholder = _('Please enter a patron card number or an item barcode.');
    this.searchText = '';
    this.router.navigate([], { queryParams: {}});
  }

  removeLoan(loan: Loan) {}

  applyLoans(loans: Loan[]) {
    const observables = [];
    for (const loan of loans) {
      if (loan.currentAction !== LoanAction.no) {
        observables.push(this.loansService.doAction(loan));
      }
    }
    forkJoin(observables).subscribe(
      (newLoans) => {
        this.patron.loans = this.patron.loans.map(loan => {
          const newLoan = newLoans.filter(l => l.loan_pid === loan.loan_pid).pop();
          if (newLoan) {
            newLoan.item = loan.item;
            return newLoan;
          }
          return loan;
        });
      },
      (err) => this.addAlert('danger', _('an error occurs on the server: ' + err))
    );
  }

  addAlert(type, message) {
    this.alerts.push({
      type: type,
      msg: message,
      timeout: this.alertTimeout
    });
  }
}
