import { Injectable } from '@angular/core';

@Injectable()
export class ApiService {

  private entryPoints = {
    'circulation-policy': '/api/circ_policies/',
    'item': '/api/item/',
    'item-type': '/api/item_types/',
    'library': '/api/libraries/',
    'organisation': '/api/organisations/',
    'patron-type': '/api/patron_types/',
    'user': '/api/users/'
  };

  private baseUrl: string = null;

  constructor() { }

  public setBaseUrl(baseUrl: string): void {
    this.baseUrl = baseUrl;
  }

  public getApiEntryPointByType(type: string, absolute: boolean = false) {
    if (!(type in this.entryPoints)) {
      throw new Error('Api Service: type not found.');
    }
    let entryPoint = this.entryPoints[type];
    if (absolute) {
      entryPoint = this.baseUrl + entryPoint;
    }
    return entryPoint;
  }
}
