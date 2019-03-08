import { Injectable } from '@angular/core';
import { FormBuilder, Validators } from '@angular/forms';
import { CirculationPolicy } from './circulation-policy';
import { PatronTypeTool } from '@app/core/patron-type/patron-type-tool';
import { ItemTypeTool, ApiService } from '@app/core';

@Injectable()
export class CirculationPolicyFormService {

  private form;

  constructor(
    private apiService: ApiService,
    private fb: FormBuilder,
    private patronTypeTool: PatronTypeTool,
    private itemTypeTool: ItemTypeTool
    ) {
    this.build();
    this.validators();
  }

  public populate(circulation: CirculationPolicy) {
    this.form.patchValue({
      name: circulation.name,
      description: circulation.description,
      allow_checkout: circulation.allow_checkout,
      checkout_duration: circulation.checkout_duration,
      allow_requests: circulation.allow_requests,
      number_renewals: circulation.number_renewals,
      renewal_duration: circulation.renewal_duration,
      policy_library_level: circulation.policy_library_level,
      is_default: circulation.is_default,
      settings: this.unserializeSettings(circulation.settings)
    });
    if ('libraries' in circulation) {
      this.form.get('libraries').setValue(
        this.unserializeLibraries(circulation.libraries)
      );
    }
  }

  public getForm() {
    return this.form;
  }

  private build() {
    this.form = this.fb.group({
      name: [null, [
        Validators.required,
        Validators.minLength(2)
      ]],
      description: [null, [
        Validators.required
      ]],
      allow_requests: [true],
      allow_checkout: [true],
      checkout_duration: [7],
      number_renewals: [0],
      renewal_duration: [null],
      policy_library_level: [false],
      is_default: [],
      libraries: [],
      settings: []
    });
  }

  private validators() {
    const checkoutDurationControl = this.getControlByFieldName('checkout_duration');
    const numberRenewalsControl = this.getControlByFieldName('number_renewals');
    this.form.get('allow_checkout').valueChanges.subscribe(checkout => {
      if (checkout) {
        checkoutDurationControl.setValidators([
          Validators.required,
          Validators.min(1)
        ]);
        numberRenewalsControl.setValidators([
          Validators.required,
          Validators.min(0)
        ]);
      } else {
        checkoutDurationControl.clearValidators();
        numberRenewalsControl.clearValidators();
      }
    });
    const renewalDuration = this.getControlByFieldName('renewal_duration');
    numberRenewalsControl.valueChanges.subscribe(renewals => {
      if (renewals > 0) {
        renewalDuration.setValidators([
          Validators.required,
          Validators.min(1)
        ]);
      } else {
        renewalDuration.clearValidators();
      }
    });
  }

  getControlByFieldName(fieldName: string) {
    return this.form.get(fieldName);
  }

  getValues() {
    const formValues = this.form.value;
    formValues.libraries = this.serializeLibraries(formValues.libraries);
    formValues.settings = this.serializeSettings(formValues.settings);
    return formValues;
  }

  private unserializeLibraries(libraries) {
    const ulibraries = [];
    const librariesRegex = new RegExp(
      this.apiService.getApiEntryPointByType('libraries', true) + '(.+)$'
    );
    libraries.forEach(element => {
      ulibraries.push(
        element['$ref'].match(librariesRegex)[1]
      );
    });
    return ulibraries;
  }

  private serializeLibraries(libraries) {
    const libraryEntryPoint = this.apiService
      .getApiEntryPointByType('libraries', true);
    const slibraries = [];
    libraries.forEach(element => {
      slibraries.push({
        $ref: libraryEntryPoint + element
      });
    });
    return slibraries;
  }

  private unserializeSettings(settings) {
    const itemTypeRegex = new RegExp(
      this.apiService.getApiEntryPointByType('item_types', true) + '(.+)$'
    );
    const patronTypeRegex = new RegExp(
      this.apiService.getApiEntryPointByType('patron_types', true) + '(.+)$'
    );
    const mapping = [];
    settings.forEach(element => {
      const pkey = this.patronTypeTool.generatePatronTypeKey(
        element.patron_type['$ref'].match(patronTypeRegex)[1]
      );
      if (!(pkey in mapping)) {
        mapping[pkey] = [];
      }
      mapping[pkey].push(this.itemTypeTool.generateItemTypeKey(
        element.item_type['$ref'].match(itemTypeRegex)[1]
      ));
    });
    return mapping;
  }

  private serializeSettings(settings) {
    const patronTypeentrypoint = this.apiService
      .getApiEntryPointByType('patron_types', true);
    const itemTypeentrypoint = this.apiService
      .getApiEntryPointByType('item_types', true);
    const mapping = [];
    Object.keys(settings).forEach(function(key) {
      settings[key].forEach(element => {
        mapping.push({
          patron_type: {
            $ref: patronTypeentrypoint + key.substr(1, key.length - 1)
          },
          item_type: {
            $ref: itemTypeentrypoint + element.substr(1, key.length - 1)
          }
        });
      });
    });
    return mapping;
  }
}
