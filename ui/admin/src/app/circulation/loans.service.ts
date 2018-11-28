import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Loan } from './loans';
// import { Patron } from './patron';
import * as moment from 'moment';
import { BehaviorSubject, of, forkJoin } from 'rxjs';
import { mergeMap, map } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class LoansService {
  returned_loans: BehaviorSubject<Loan[]>;
  constructor(
    private http: HttpClient
    ) {
    this.returned_loans = new BehaviorSubject<Loan[]>([]);
  }

  getRequestedLoans(libraryPid) {
    return this.http
    .get<Loan[]>('/items/loan/requested_loans/' + libraryPid)
    .pipe(
      map(res => res.map(loan => new Loan(loan)))
    );
  }

  doAction(loan) {
    const action = loan.currentAction;
    const action_url = loan.links.actions[action].replace(/^(?:\/\/|[^\/]+)*\//, '');
    if (action && action_url) {
      console.log(action, action_url);
    }
    return this.http.put<any>(action_url, {loan_pid: loan.loan_pid, item_pid: loan.item_pid}).pipe(
      map(data => {
        const newLoan = new Loan(data);
        newLoan.actionDone = action;
        return newLoan;
      })
      );
    // return new BehaviorSubject(new Loan());
  }

  doValidateRequest(loan) {
    const action_url = loan.links.actions.validate.replace(/^(?:\/\/|[^\/]+)*\//, '');
    return this.http.put<any>(action_url, {loan_pid: loan.loan_pid, item_pid: loan.item_pid});
  }
}
