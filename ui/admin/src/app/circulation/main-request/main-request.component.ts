import { Component, OnInit } from '@angular/core';
import { Loan } from '../loans';
import { LoansService } from '../loans.service';
import { UserService } from '../../user.service';
import { AlertComponent } from 'ngx-bootstrap/alert/alert.component';
import { TranslateStringService } from '../../translate-string.service';

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
  public loans: Loan[] = null;
  private library_pid: string;
  public alerts: any[] = [];

  constructor (
    private currentUser: UserService,
    private loansService: LoansService,
    private translate: TranslateStringService
  ) {}

  onAlertClosed(dismissedAlert: AlertComponent): void {
    this.alerts = this.alerts.filter(alert => alert !== dismissedAlert);
  }

  ngOnInit() {
    this.currentUser.loggedUser.subscribe(user => {
      if (user && user.library_pid) {
        this.library_pid = user.library_pid;
        this.loans = null;
        this.getRequestedLoans();
      }
    });
  }

  getRequestedLoans() {
    this.loansService.getRequestedLoans(this.library_pid).subscribe(loans => {
      this.loans = loans;
    });
  }

  searchValueUpdated(search_text: string) {
    this.searchText = search_text;
    const loan = this.loans.find(l => l.item_barcode === search_text);
    if (loan === undefined) {
      this.alerts.push({
        type: 'danger',
        msg: _('request not found'),
        timeout: 5000
      });
    } else {
      const loans = this.loans;
      this.loans = null;
      this.loansService.doValidateRequest(loan).subscribe(
        newLoan => {
          newLoan = newLoan;
          this.loans = loans.map(l => {
            if (l.loan_pid === newLoan.loan_pid) {
              return new Loan(newLoan);
            }
            return l;
          });
          this.alerts.push({
            type: 'info',
            msg: this.translate.trans(_('The item is ')) + this.translate.trans(newLoan.state),
            timeout: 5000
          });
          this.searchText = '';
        }
      );
    }
  }
}
