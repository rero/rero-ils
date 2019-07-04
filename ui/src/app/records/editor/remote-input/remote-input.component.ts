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

import { AbstractControl } from '@angular/forms';
import { Component, Input, OnInit } from '@angular/core';
import { JsonSchemaFormService } from 'angular6-json-schema-form';
import { of } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { RecordsService } from '../../records.service';


@Component({
  // tslint:disable-next-line:component-selector
  selector: 'app-remote-input',
  templateUrl: './remote-input.component.html',
  styleUrls: ['./remote-input.component.scss']
})
export class RemoteInputComponent implements OnInit {
  formControl: AbstractControl;
  controlName: string;
  controlValue: string;
  controlDisabled = false;
  boundControl = false;
  options: any;
  autoCompleteList: string[] = [];
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
    if (this.options.remoteRecordType) {
        this.formControl.setAsyncValidators([
            this.valueAlreadyTaken.bind(this, this.options.remoteRecordType)
        ]);
    }
  }

  updateValue(event) {
    this.jsf.updateValue(this, event.target.value);
  }

  valueAlreadyTaken(recordType: string, control: AbstractControl) {
    const pid = control.root.value.pid;
    return this.recordsService.valueAlreadyExists(
        recordType, this.controlName, control.value, pid);
  }

}
