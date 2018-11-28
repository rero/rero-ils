import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Subject, BehaviorSubject } from 'rxjs';

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

  private librariesUrl = '/api/libraries';

  currentLibrary: Subject<Library> = new BehaviorSubject<Library>(null);

  constructor(
    private client: HttpClient,
    private browser: BrowserService
  ) { }

  loadLibrary(pid: number) {
    this.client.get<Library>(this.librariesUrl + '/' + pid, httpOptions).subscribe(library => {
      this.setCurrentLibrary(library);
    });
  }

  setCurrentLibrary(library: Library) {
    this.currentLibrary.next(new Library(library));
  }

  save(library: Library, redirectUrl?) {
    const library_id = library['id'];
    if (environment.production) {
      delete library['id'];
    }
    this.client.put<Library>(this.librariesUrl + '/' + library_id, library, httpOptions).subscribe(
      lib => {
        this.setCurrentLibrary(lib);
        if (environment.production && redirectUrl) {
          this.browser.redirect(redirectUrl);
        }
      }
    );
  }
}
