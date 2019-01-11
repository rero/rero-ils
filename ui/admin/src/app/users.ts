import { Loan } from './circulation/loans';

export interface Library {
  pid: string;
  organisation: Organisation;
}

export interface Organisation {
  pid: string;
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
  postal_code: string;
  roles: [];
  street: string;
  organisation_pid: string;
  barcode?: string;
  loans?: Loan[];

  constructor(obj?: any) {
    Object.assign(this, obj);
  }
}

export interface UserSettings {
  language: string;
  baseUrl: string;
}
