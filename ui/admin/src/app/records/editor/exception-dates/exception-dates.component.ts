import { AbstractControl, FormArray } from '@angular/forms';
import { Component, Input, OnInit } from '@angular/core';
import { JsonSchemaFormService } from 'angular6-json-schema-form';
import { of } from 'rxjs';
import { debounceTime } from 'rxjs/operators';
import { RecordsService } from '../../records.service';
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { ExceptionDatesEditComponent } from './exception-dates-edit.component';
import { ChangeDetectorRef } from '@angular/core'
import _ from 'lodash';

@Component({
  // tslint:disable-next-line:component-selector
  selector: 'app-exception-dates',
  templateUrl: './exception-dates.component.html',
  styleUrls: ['./exception-dates.component.scss']
})
export class ExceptionDatesComponent implements OnInit {
  formControl: FormArray;
  controlName: string;
  controlValue: any[];
  controlDisabled = false;
  boundControl = false;
  options: any;
  @Input() layoutNode: any;
  @Input() layoutIndex: number[];
  @Input() dataIndex: number[];
  bsModalRef: BsModalRef;
  exceptionDates = [];
  constructor(
    private jsf: JsonSchemaFormService,
    private recordsService: RecordsService,
    private modalService: BsModalService,
    private ref: ChangeDetectorRef
    ) { }

  ngOnInit() {
    this.options = this.layoutNode.options || {};
    this.jsf.initializeControl(this, false);
    if (this.controlValue.length && this.controlValue[0].title === null) {
       this.controlValue.splice(0, 1);
    }
    this.exceptionDates = this.controlValue;
  }

  addException() {

    this.bsModalRef = this.modalService.show(ExceptionDatesEditComponent, {
      initialState: {exceptionDate: null},
      class: 'modal-lg',
      backdrop: 'static'
    });

    this.bsModalRef.content.value.subscribe(value =>
    {
      this.exceptionDates.push(value);
      this.jsf.updateValue(this, this.exceptionDates);
      // force ui update
      this.ref.markForCheck();
    });

  }

  editException(index) {
    this.bsModalRef = this.modalService.show(ExceptionDatesEditComponent, {
      initialState: {exceptionDate: this.controlValue[index]},
      class: 'modal-lg',
      backdrop: 'static'
    });
    this.bsModalRef.content.value.subscribe(value =>
      {
        this.exceptionDates[index] = value;
        this.jsf.updateValue(this, this.exceptionDates);
        // force ui update
        this.ref.markForCheck();
      });
  }

  deleteException(index) {
    this.exceptionDates.splice(index, 1);
    this.jsf.updateValue(this, this.exceptionDates);
  }
}
