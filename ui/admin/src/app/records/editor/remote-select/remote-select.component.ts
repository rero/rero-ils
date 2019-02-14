import { AbstractControl } from '@angular/forms';
import { buildTitleMap, isArray } from 'angular6-json-schema-form';
import { Component, Input, OnInit } from '@angular/core';
import { JsonSchemaFormService } from 'angular6-json-schema-form';
import { RecordsService } from '../../records.service';
import { ApiService } from '@app/core';

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
    private recordsService: RecordsService,
    private apiService: ApiService
    ) { }

  ngOnInit() {
    this.options = this.layoutNode.options || {};
    // new option

    const remoteRecordType = this.options.remoteRecordType;
    if (remoteRecordType) {
      this.recordsService.getRecords(remoteRecordType).subscribe(data => {
        data.hits.hits.map(record => {
          const urlPrefix = this.apiService.getApiEntryPointByType(remoteRecordType, true);
          this.selectList.push({
            'name': record.metadata['name'],
            'value': `${urlPrefix}/${record['metadata']['pid']}`
          });
        });
        this.jsf.initializeControl(this);
        this.formControl.setValue(null);
        // NOTE: default is not supported yet as it does not make sense

        if (this.controlValue) {
          this.formControl.setValue(this.controlValue);
        } else {
          if (this.options.placeHolder) {
            this.selectList.unshift({
              name: this.options.placeHolder,
              value: ''
            });
          }
          this.formControl.setValue(this.selectList[0]['value']);
        }
      });
    } else {
      this.selectList = buildTitleMap(
        this.options.titleMap || this.options.enumNames,
        this.options.enum, !!this.options.required, !!this.options.flatList
        );
      this.jsf.initializeControl(this);
      if (!this.controlValue) {
        if (this.options.default) {
          this.formControl.setValue(this.options.default);
        } else {
          if (this.options.placeHolder) {
            this.selectList.unshift({
              name: this.options.placeHolder,
              value: ''
            });
          }
          this.formControl.setValue(this.selectList[0]['value']);
        }
      }
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
