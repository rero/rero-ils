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

import { AbstractControl } from '@angular/forms';
import { Component, Input, OnInit } from '@angular/core';
import { JsonSchemaFormService, hasOwn } from 'angular6-json-schema-form';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  // tslint:disable-next-line:component-selector
  selector: 'app-submit',
  templateUrl: './submit.component.html',
  styleUrls: ['./submit.component.scss'],
})
export class SubmitComponent implements OnInit {
  formControl: AbstractControl;
  controlName: string;
  controlValue: any;
  controlDisabled = false;
  boundControl = false;
  options: any;
  @Input() layoutNode: any;
  @Input() layoutIndex: number[];
  @Input() dataIndex: number[];
  formValidCode = 'VALID';

  constructor(
    private jsf: JsonSchemaFormService
  ) { }

  ngOnInit() {
    this.options = this.layoutNode.options || {};
    this.jsf.initializeControl(this);
    if (hasOwn(this.options, 'disabled')) {
      this.controlDisabled = this.options.disabled;
    } else if (this.jsf.formOptions.disableInvalidSubmit) {
      this.controlDisabled = !(this.jsf.isValid && this.jsf.formGroup.status === this.formValidCode);
      combineLatest(this.jsf.isValidChanges, this.jsf.formGroup.statusChanges)
      .subscribe(([jsonSchemaValidChanges, formValidChanges]) => {
          this.controlDisabled = !(jsonSchemaValidChanges && formValidChanges === this.formValidCode);
      });
    }
    if (this.controlValue === null || this.controlValue === undefined) {
      this.controlValue = this.options.title;
    }
  }

  updateValue(event) {
    if (typeof this.options.onClick === 'function') {
      this.options.onClick(event);
    } else {
      this.jsf.updateValue(this, event.target.value);
    }
  }
}
