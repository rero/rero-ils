import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of, forkJoin } from 'rxjs';
import { map, concatAll, mergeMap } from 'rxjs/operators';
import { User, UserSettings } from './users';
import { Item } from './circulation/items';
import { RecordsService } from './records/records.service';


@Injectable({
  providedIn: 'root'
})
export class UserService {

  loggedUser: BehaviorSubject<User> = new BehaviorSubject<User>(null);
  userSettings: BehaviorSubject<any> = new BehaviorSubject(null);

  constructor(
    private http: HttpClient,
    private recordService: RecordsService
    ) {
    this.http.get<any>('/patrons/logged_user?resolve')
    .subscribe(data => {
      this.loggedUser.next(new User(data.metadata));
      this.userSettings.next(<UserSettings>data.settings);
    });
  }

  getUser(pid: string) {
    return this.recordService.getRecord('patrons', pid, 1).pipe(
      map(data => {
        if (data) {
          const patron = new User(data.metadata);
          return forkJoin(
              of(patron),
              this.recordService.getRecord('patron_types', patron.patron_type.pid)
              ).pipe(
                map(patronAndType => {
                  const newPatron = patronAndType[0];
                  const patron_type = patronAndType[1];
                  if (patron_type) {
                    newPatron.patron_type = patron_type.metadata;
                  }
                  return newPatron;
                })
          );
        }
      }),
      concatAll()
    );
  }

  getPatron(barcode: string): Observable<any> {
    return this.http
    .get<any>('/api/patrons/?q=barcode:' + barcode)
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
              this.getItems(patron.pid),
              this.recordService.getRecord('patron_types', patron.patron_type.pid)
              ).pipe(
                map(data => {
                  const newPatron = data[0];
                  const items = data[1];
                  const patron_type = data[2];
                  newPatron.items = items;
                  if (patron_type) {
                    newPatron.patron_type = patron_type.metadata;
                  }
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

  getItems(patronPid: string) {
    const url = `/api/item/loans/${patronPid}`;
    return this.http.get<any>(url).pipe(
      map( data => data.hits),
      map(hits => hits.total === 0 ? [] : hits.hits),
      map(hits => hits.map(data => {
          const item = new Item(data.item);
          if (data.loan) {
            item.setLoan(data.loan);
          }
          return item;
        })
      )
    );
  }

  getItem(item_pid: string) {
    return this.http.get<any>('/api/items/?q=pid:' + item_pid)
    .pipe(
      map(response => new Item(response.hits.hits[0].metadata))
    );
  }

}
