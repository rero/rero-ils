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
import { buildTitleMap, isArray } from 'angular6-json-schema-form';
import { Component, Input, OnInit } from '@angular/core';
import { JsonSchemaFormService } from 'angular6-json-schema-form';
import { RecordsService } from '@app/records/records.service';
import { _ } from '@app/circulation/main-request/main-request.component';
import { of } from 'rxjs';

@Component({
  selector: 'app-select-item-type-type',
  templateUrl: './select-item-type-type.component.html',
  styleUrls: ['./select-item-type-type.component.scss']
})
export class SelectItemTypeTypeComponent implements OnInit {
  formControl: AbstractControl;
  controlName: string;
  controlValue: any;
  controlDisabled = false;
  boundControl = false;
  options: any;
  selectList: any[] = [];
  isArray = isArray;
  @Input() layoutNode: any;
  @Input() layoutIndex: number[];
  @Input() dataIndex: number[];

  constructor(
    private jsf: JsonSchemaFormService,
    private recordsService: RecordsService
  ) { }

  ngOnInit() {
    this.options = this.layoutNode.options || {};
    this.selectList = buildTitleMap(
      this.options.titleMap || this.options.enumNames,
      this.options.enum, !!this.options.required, !!this.options.flatList
    );
    this.jsf.initializeControl(this);
    if (this.options.default) {
      this.formControl.setValue(this.options.default);
    }
    this.formControl.setAsyncValidators([
      this.typeValidator.bind(this)
    ]);
  }

  updateValue(event) {
    this.jsf.updateValue(this, event.target.value);
  }

  typeValidator(control: AbstractControl) {
    const pid = control.root.value.pid;
    const type = control.value;
    if (type === 'online') {
      return this.recordsService.valueAlreadyExists(
        'item_types',
        'type',
        control.value,
        pid
      );
    } else {
      return of(true);
    }
  }
}
