import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Subject, BehaviorSubject } from 'rxjs';

import { environment } from '../../environments/environment';

import { Library } from './library';
import { BrowserService } from '../browser.service';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { UserService } from '../user.service';
import { User } from '../users';

const httpOptions = {
  headers: new HttpHeaders({
    'Accept': 'application/rero+json',
    'Content-Type': 'application/json'
  })
};

@Injectable()
export class LibrariesService {

  private librariesUrl = '/api/libraries';

  private loggedUser: User;

  currentLibrary: BehaviorSubject<Library> = new BehaviorSubject<Library>(null);

  constructor(
    private client: HttpClient,
    private browser: BrowserService,
    private user: UserService
  ) {
    this.user.loggedUser.subscribe(loggedUser => this.loggedUser = loggedUser);
  }

  loadLibrary(pid: number) {
    this.client.get<Library>(this.librariesUrl + '/' + pid, httpOptions).subscribe(library => {
      this.setCurrentLibrary(library);
    });
  }

  setCurrentLibrary(library: Library) {
    this.currentLibrary.next(new Library(library));
  }

  checkIfCodeAlreadyTaken(code: string): Observable<Boolean> {
    return this.client.get<any>(
        this.librariesUrl + '/?q=code:' + code +
        '&libraries.code:' + this.loggedUser.organisation_pid +
        '&size=0'
      ).pipe(map(response => {
        if (
          this.currentLibrary === null
          || this.currentLibrary.getValue().code !== code
        ) {
          return response.hits.total >= 1;
        }
      }
    ));
  }

  save(library: Library) {
    const baseUpdate = '/admin/lib/ajax/update/';
    const baseRedirect = '/libraries/';
    if (environment.production) {
      delete library['id'];
    }
    this.client.post<Library>(baseUpdate, library, httpOptions).subscribe(
      lib => {
        this.setCurrentLibrary(lib);
        if (environment.production) {
          this.browser.redirect(baseRedirect + lib.pid);
        }
      }
    );
  }
}
