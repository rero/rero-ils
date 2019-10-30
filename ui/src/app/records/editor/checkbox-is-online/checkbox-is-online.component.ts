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

import { Component, OnInit, Input } from '@angular/core';
import { AbstractControl } from '@angular/forms';
import { JsonSchemaFormService } from 'angular6-json-schema-form';
import { of } from 'rxjs';
import { RecordsService } from '@app/records/records.service';

@Component({
  selector: 'app-checkbox-is-online',
  templateUrl: './checkbox-is-online.component.html',
  styleUrls: ['./checkbox-is-online.component.scss']
})
export class CheckboxIsOnlineComponent implements OnInit {
  formControl: AbstractControl;
  controlName: string;
  controlValue: any;
  controlDisabled = false;
  boundControl = false;
  options: any;
  trueValue: any = true;
  falseValue: any = false;
  @Input() layoutNode: any;
  @Input() layoutIndex: number[];
  @Input() dataIndex: number[];

  constructor(
    private jsf: JsonSchemaFormService,
    private recordsService: RecordsService
  ) { }

  ngOnInit() {
    this.options = this.layoutNode.options || {};
    this.jsf.initializeControl(this);
    if (this.controlValue === null || this.controlValue === undefined) {
      this.controlValue = this.options.title;
    }
    this.formControl.setAsyncValidators([
      this.validUniqueIsOnlineLocationValidator.bind(this)
    ]);
  }

  updateValue(event) {
    event.preventDefault();
    this.jsf.updateValue(this, event.target.checked ? this.trueValue : this.falseValue);
  }

  get isChecked() {
    return this.jsf.getFormControlValue(this) === this.trueValue;
  }

  validUniqueIsOnlineLocationValidator(control: AbstractControl) {
    if (this.isChecked) {
      const values = control.root.value;
      return this.recordsService.uniqueIsOnlineLocationValidator(
        values.library.$ref,
        values.pid
      );
    } else {
      // return observable that emits default value to async validator
      return of(null);
    }
  }
}
