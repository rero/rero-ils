import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

import { environment } from '../../environments/environment';

import { Library } from './library';
import { BrowserService } from '../browser.service';

const httpOptions = {
  headers: new HttpHeaders({
    'Accept': 'application/rero+json',
    'Content-Type': 'application/json'
  })
};

@Injectable()
export class LibrariesService {

  private librariesUrl = '/api/libraries/';

  currentLibrary: BehaviorSubject<Library> = new BehaviorSubject<Library>(null);

  constructor(
    private client: HttpClient,
    private browser: BrowserService
  ) { }

  loadLibrary(pid: number) {
    this.client.get<Library>(this.librariesUrl + pid, httpOptions).subscribe(library => {
      this.setCurrentLibrary(library);
    });
  }

  setCurrentLibrary(library: Library) {
    this.currentLibrary.next(new Library(library));
  }

  checkIfCodeAlreadyTaken(organisationId: string, code: string) {
    // TODO: Missing OrganisationId on json schema library to check organisation
    return this.client.get(
      this.librariesUrl + '?q=code:' + code
    );
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
