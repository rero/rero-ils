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

export interface Library {
  pid: string;
  organisation: Organisation;
}

export interface Organisation {
  pid: string;
}

export interface PatronType {
  pid: string;
  name?: string;
}

export class User {
  $schema: string;
  birth_date: string;
  city: string;
  email: string;
  first_name: string;
  is_patron: boolean;
  last_name: string;
  library: Library;
  name: string;
  phone: string;
  pid: string;
  circulation_location_pid?: string;
  postal_code: string;
  roles: [];
  street: string;
  organisation_pid: string;
  barcode?: string;
  settings: UserSettings;
  items?: any[];
  patron_type?: PatronType;

  constructor(obj?: any) {
    Object.assign(this, obj);
  }
}

export interface UserSettings {
  language: string;
  baseUrl: string;
}
