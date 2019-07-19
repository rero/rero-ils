import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class OrganisationViewService {

  private viewCode = 'global';

  constructor() { }

  setViewCode(viewcode: string) {
    this.viewCode = viewcode;
  }

  getViewCode() {
    return this.viewCode;
  }
}
