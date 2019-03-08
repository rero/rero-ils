export interface Organisation {
  $ref: string;
}

export class CirculationPolicy {
  $schema: string = null;
  id: number = null;
  pid: number = null;
  name: string = null;
  description: string = null;
  organisation: Organisation;
  allow_requests: boolean = null;
  allow_checkout: boolean = null;
  checkout_duration: number = null;
  number_renewals: number = null;
  renewal_duration: number = null;
  policy_library_level: boolean = null;
  is_default: boolean = null;
  libraries: Array<any> = [];
  settings: Array<any> = [];

  constructor(obj?: any) {
    this.setDefault();
    if (obj) {
      this.update(obj);
    }
  }

  setDefault() {
    this.allow_requests = true;
    this.allow_checkout = true;
    this.checkout_duration = 7;
    this.number_renewals = 0;
    this.policy_library_level = false;
    this.is_default = false;
    this.organisation = {
      $ref: null
    };
    this.libraries = [];
    this.settings = [];
  }

  update(obj) {
    Object.assign(this, obj);
  }
}
