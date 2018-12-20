import { Component, OnInit, Input } from '@angular/core';
import { BsModalService, BsModalRef } from 'ngx-bootstrap/modal';
import { ExceptionDatesEditComponent } from '../exception-dates-edit/exception-dates-edit.component';

@Component({
  selector: 'libraries-exception-dates-list',
  templateUrl: './exception-dates-list.component.html',
  styleUrls: ['./exception-dates-list.component.scss']
})
export class ExceptionDatesListComponent implements OnInit {

  bsModalRef: BsModalRef;

  @Input() library;

  constructor(private modalService: BsModalService) { }

  ngOnInit() {
  }

  addException() {
    this.bsModalRef = this.modalService.show(ExceptionDatesEditComponent, {
      initialState: {index: null},
      class: 'modal-lg',
      backdrop: 'static'
    });
    return false;
  }

  editException(index) {
    this.bsModalRef = this.modalService.show(ExceptionDatesEditComponent, {
      initialState: {index: index},
      class: 'modal-lg',
      backdrop: 'static'
    });
    return false;
  }

  deleteException(index) {
    this.library.deleteException(index);
  }
}
