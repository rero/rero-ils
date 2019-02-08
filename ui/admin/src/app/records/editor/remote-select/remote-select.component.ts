import { AbstractControl, } from '@angular/forms';
import { buildTitleMap, isArray } from 'angular6-json-schema-form';
import { Component, Input, OnInit } from '@angular/core';
import { JsonSchemaFormService } from 'angular6-json-schema-form';
import { RecordsService } from '../../records.service';

@Component({
    selector: 'app-remote-select',
    templateUrl: './remote-select.component.html',
    styleUrls: ['./remote-select.component.scss']
})
export class RemoteSelectComponent implements OnInit {

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
    // new option
    const remoteRecordType = this.options.remoteRecordType;
    if (remoteRecordType) {
      this.recordsService.getRecords(remoteRecordType).subscribe(data => {
        data.hits.hits.map(record => {
          this.selectList.push({
            'name': record.metadata['name'],
            'value': `http://ils.rero.ch/api/${remoteRecordType}/${record['metadata']['pid']}`
          });
        });
        this.jsf.initializeControl(this);
        if (this.controlValue) {
          this.formControl.setValue(this.controlValue);
        } else {
          this.formControl.setValue(this.selectList[0]['value']);
        }
      });
    } else {
      this.selectList = buildTitleMap(
        this.options.titleMap || this.options.enumNames,
        this.options.enum, !!this.options.required, !!this.options.flatList
      );
      this.jsf.initializeControl(this);
      this.formControl.setValue(this.selectList[0]['value']);
    }
    // patch
    if (this.options.readonly) {
      this.formControl.disable();
    }
  }

  updateValue(event) {
    this.jsf.updateValue(this, event.target.value);
  }
}
