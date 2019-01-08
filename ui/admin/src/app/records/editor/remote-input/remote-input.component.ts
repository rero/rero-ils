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
