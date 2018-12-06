import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of, forkJoin } from 'rxjs';
import { map, concatAll, mergeMap } from 'rxjs/operators';
import { User } from './users';
import { Loan, Item } from './circulation/loans';

@Injectable({
  providedIn: 'root'
})
export class UserService {

  loggedUser: BehaviorSubject<User> = new BehaviorSubject<User>(null);

  constructor(private http: HttpClient) {
    this.http.get<User>('/patrons/logged_user')
    .subscribe(user => {
      this.loggedUser.next(new User(user));
    });
  }

  getPatron(card_number: string): Observable<any> {
    return this.http
    .get<any>('/api/patrons/?q=barcode:' + card_number)
    .pipe(
      map(response => {
        switch (response.hits.total) {
          case 0: {
            return of(null);
            break;
          }
          case 1: {
            const patron = new User(response.hits.hits[0].metadata);
            return forkJoin(
              of(patron),
              this.getLoans(patron.pid)
              ).pipe(
                map(data => {
                  const newPatron = data[0];
                  const loans = data[1];
                  newPatron.loans = <Loan[]>loans;
                  return newPatron;
                })
              );
              break;
            }
            default: {
              throw new Error('too much results');
              break;
            }
          }
        }
      ),
      concatAll()
    );
  }

  getLoans(patron_pid: string) {
    return this.http.get<any>('/api/circulation/loans/?q=state:ITEM_ON_LOAN%20AND%20patron_pid:' + patron_pid)
    .pipe(
      map(response => {
        return forkJoin(response.hits.hits.map(loan => {
          loan = new Loan(loan.metadata);
          return forkJoin(
              of(loan),
              this.getItem(loan.item_pid)
          ).pipe(
            map(data => {
              const newLoan = data[0];
              newLoan.item = data[1];
              return newLoan;
            })
          );
        }));
      }
    ),
    mergeMap(data => data));
  }

  getItem(item_pid: string) {
    return this.http.get<any>('/api/items/?q=pid:' + item_pid)
    .pipe(
      map(response => new Item(response.hits.hits[0].metadata))
    );
  }

}
