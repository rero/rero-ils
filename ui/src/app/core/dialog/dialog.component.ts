import { Component, OnInit } from '@angular/core';
import { Subject } from 'rxjs';
import { BsModalRef } from 'ngx-bootstrap';

@Component({
  selector: 'app-dialog',
  templateUrl: './dialog.component.html',
  styleUrls: ['./dialog.component.scss']
})
export class DialogComponent implements OnInit {

  public title: string;
  public body: string;
  public cancelTitleButton: string;
  public confirmTitleButton: string;
  public confirmButton: boolean;

  public onClose: Subject<boolean>;

  constructor(private _bsModalRef: BsModalRef) { }

  ngOnInit() {
    this.onClose = new Subject();
  }

  confirm(): void {
    this.onClose.next(true);
    this._bsModalRef.hide();
  }

  decline(): void {
    this.onClose.next(false);
    this._bsModalRef.hide();
  }
}
