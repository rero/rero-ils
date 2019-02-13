import { Injectable } from '@angular/core';

@Injectable()
export class ApiService {

  private entryPoints = {
    'circ_policies': '/api/circ_policies/',
    'documents': '/api/documents/',
    'items': '/api/items/',
    'item_types': '/api/item_types/',
    'loans': '/api/loans/',
    'libraries': '/api/libraries/',
    'locations': '/api/locations/',
    'organisations': '/api/organisations/',
    'patron_types': '/api/patron_types/',
    'patrons': '/api/patrons/',
    'persons': '/api/persons/'
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
