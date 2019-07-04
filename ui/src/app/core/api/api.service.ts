/*

RERO ILS
Copyright (C) 2019 RERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

*/

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
