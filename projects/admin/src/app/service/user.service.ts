/*
 * RERO ILS UI
 * Copyright (C) 2019 RERO
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import { Injectable, EventEmitter } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AppConfigService } from './app-config.service';
import { User } from '../class/user';
import { concatAll, map } from 'rxjs/operators';
import { Observable, forkJoin, of } from 'rxjs';
import { Item } from '../circulation/items';
import { RecordService } from '@rero/ng-core';

@Injectable({
  providedIn: 'root'
})
export class UserService {

  readonly onUserLoaded: EventEmitter<User> = new EventEmitter();

  private user: User;

  constructor(
    private http: HttpClient,
    private appConfigService: AppConfigService,
    private recordService: RecordService
  ) { }

  getCurrentUser() {
    return this.user;
  }

  public loadLoggedUser() {
    this.http.get<any>('/patrons/logged_user?resolve').subscribe(data => {
      let user = null;
      if (data.metadata) {
        user = new User(data.metadata);
        user.is_logged = true;
      } else {
        user = new User({});
      }
      this.appConfigService.setSettings(data.settings);
      this.user = user;
      this.onUserLoaded.emit(user);
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
                  const patronType = patronAndType[1];
                  if (patronType) {
                    newPatron.patron_type = patronType.metadata;
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
                  const patronType = data[2];
                  newPatron.items = items;
                  if (patronType) {
                    newPatron.patron_type = patronType.metadata;
                  }
                  return newPatron;
                })
              );
            }
            default: {
              throw new Error('too much results');
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

  getItem(itemPid: string) {
    return this.http.get<any>('/api/items/?q=pid:' + itemPid)
    .pipe(
      map(response => new Item(response.hits.hits[0].metadata))
    );
  }

}
