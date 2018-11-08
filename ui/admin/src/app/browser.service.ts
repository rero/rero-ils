import { Inject, Injectable, InjectionToken } from '@angular/core';
import { DOCUMENT } from '@angular/common';

@Injectable({
  providedIn: 'root'
})
export class BrowserService {

  constructor(@Inject(DOCUMENT) private document: any) { }

  get origin() { return this.document.location.origin; }

  fullPath(path: string) {
    return this.origin + path;
  }

  redirect(path: string) {
    this.document.location.href = this.fullPath(path);
  }
}
