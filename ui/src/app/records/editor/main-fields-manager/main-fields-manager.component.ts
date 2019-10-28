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
along with this program. If not, see <http://www.gnu.org/licenses/>.

*/

import { Component, OnInit } from '@angular/core';
import { JsonSchemaFormService, forEach, getControl } from 'angular6-json-schema-form';

@Component({
  selector: 'app-main-fields-manager',
  templateUrl: './main-fields-manager.component.html',
  styleUrls: ['./main-fields-manager.component.scss']
})
export class MainFieldsManagerComponent implements OnInit {
  // ref to field to show/hide given the key element
  private layoutRefField: any = {};

  /**
  * Constructor
  * @param jsf: angular6 jsonschema form service
  */
  constructor(private jsf: JsonSchemaFormService) { }

  /**
  * Component initialisation.
  */
  ngOnInit() {
    // keep in cache a dict with the field key name as a key and the layoutNode as a value
    let fieldToShow;
    forEach(
      this.jsf.layout,
      (v: any, k?: string | number, c?: any, rc?: any) => {
        if (c === rc) {
          // console.log('value', v, 'key', k, 'parent', c , 'root', rc);
          fieldToShow = null;
        }
        if (v instanceof Object && 'options' in v && 'show' in v.options) {
          fieldToShow = v;
        }
        if (v instanceof Object && 'dataPointer' in v && fieldToShow) {
          const pointer = v.dataPointer.split(/\//)[1];
          if (!this.layoutRefField[pointer]) {
            this.layoutRefField[pointer] = fieldToShow;
          }
        }
      },
      'top-down'
      );
      // for update only, hide non populate fields
      if (this.jsf.data && this.jsf.data.pid) {
        for (const layout of Object.keys(this.layoutRefField)) {
          if (!this.jsf.data[layout]) {
            const field = this.layoutRefField[layout];
            if (field && field.options.show === true) {
              field.options.show = false;
            }
          }
        }
      }
      // for update only, show populate fields
      for (const layout of Object.keys(this.jsf.data)) {
        const field = this.layoutRefField[layout];
        if (field && field.options.show === false) {
          field.options.show = true;
        }
      }

      // disable FormControls for hidden fields
      for (const fieldSet of Object.values(this.layoutRefField)) {
        if (this.isHidden(fieldSet)) {
          for (const field of fieldSet['items']) {
            this.disableFormGroup(field);
          }
        }
      }
    }

    /**
    * Return the list of the hidden form layout.
    * @param formLayout - object, angular6 json schema form layout
    */
    get hiddenFields() {
      return this.jsf.layout.filter(layout => this.isHidden(layout) );
    }

    /**
    * Compute the visibility of a given formLayout.
    * @param formLayout - object, angular6 json schema form layout
    */
    isHidden(formLayout) {
      return 'show' in formLayout.options && formLayout.options.show === false;
    }

    /**
    * Show a given fieldset.
    * @param formLayout - object, angular6 json schema form layout
    */
    show(formLayout) {
      formLayout.options.show = true;
      for (const item of formLayout.items) {
        this.enableFormGroup(item);
      }
    }

    /**
    * Mark a a layoutNode FormControl as enabled.
    * @param layoutNode - object, angular6 json schema form layout node
    */
    private enableFormGroup(layoutNode) {
      const control = getControl(this.jsf.formGroup, layoutNode.dataPointer);
      if (!control) {
        return false;
      }
      control.enable();
      return true;
    }

    /**
    * Mark a a layoutNode FormControl as disabled.
    * @param layoutNode - object, angular6 json schema form layout node
    */
    private disableFormGroup(layoutNode) {
      const control = getControl(this.jsf.formGroup, layoutNode.dataPointer);
      if (!control) {
        return false;
      }
      control.disable();
      return true;
    }

  }
