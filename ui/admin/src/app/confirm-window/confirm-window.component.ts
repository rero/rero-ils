import { Component, TemplateRef, Input, Output, ViewChild, EventEmitter } from '@angular/core';
import { ModalDirective } from 'ngx-bootstrap/modal';

@Component({
  selector: 'app-confirm-window',
  templateUrl: './confirm-window.component.html',
  styleUrls: ['./confirm-window.component.scss']
})
export class ConfirmWindowComponent {

 public _confirm_changes = false;

  @Output()
  public confirm = new EventEmitter<boolean>();

  @Input()
  set confirm_changes(confirm_changes: boolean) {
    this._confirm_changes = confirm_changes;
    if (confirm_changes) {
      this.childModal.show();
    } else {
        this.childModal.hide();
    }
  }
  @ViewChild('childModal') childModal: ModalDirective;


  constructor() {}

  doConfirm(ok: boolean): void {
    this.confirm.emit(ok);
      this.childModal.hide();
    }

}
