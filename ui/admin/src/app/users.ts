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
