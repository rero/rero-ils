import { Loan } from './circulation/loans';

export class User {
  $schema: string;
  birth_date: string;
  city: string;
  email: string;
  first_name: string;
  is_patron: boolean;
  is_staff: boolean;
  last_name: string;
  library_pid: string;
  name: string;
  phone: string;
  pid: string;
  postal_code: string;
  roles: [];
  street: string;
  organisation_pid: string;
  barcode?: string;
  settings: UserSettings;
  loans?: Loan[];

  constructor(obj?: any) {
    Object.assign(this, obj);
  }
}

export interface UserSettings {
  language: string;
}
