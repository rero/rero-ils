import {
  animate,
  keyframes,
  state,
  style,
  transition,
  trigger
} from '@angular/animations';
import { Component } from '@angular/core';
import { Toast, ToastrService, ToastPackage } from 'ngx-toastr';


@Component({
  selector: 'toastr-dialog-component',
  styleUrls: ['./toastr-dialog.component.scss'],
  template: `
  <div
    class="row toast show"
    role="alert"
    aria-live="assertive"
    aria-atomic="true"
    [style.display]="state.value === 'inactive' ? 'none' : ''"
  >
    <div *ngIf="message && options.enableHtml" class="toast-body" [innerHTML]="message | translate">
      <button
        type="button"
        *ngIf="options.closeButton"
        (click)="remove()"
        class="ml-2 mb-1 close"
        data-dismiss="toast"
        aria-label="Close"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
    <div *ngIf="message && !options.enableHtml" class="toast-body" translate>
      {{ message }}
      <button
        type="button"
        *ngIf="options.closeButton"
        (click)="remove()"
        class="ml-2 mb-1 close"
        data-dismiss="toast"
        aria-label="Close"
      >
        <span aria-hidden="true">&times;</span>
      </button>
    </div>
  </div>
  `,
  animations: [
    trigger('flyInOut', [
      state('inactive', style({
        opacity: 0,
      })),
      transition('inactive => active', animate('400ms ease-out', keyframes([
        style({
          transform: 'translate3d(100%, 0, 0)',
          opacity: 0,
        }),
        style({
          transform: 'none',
          opacity: 1,
        }),
      ]))),
      transition('active => removed', animate('400ms ease-out', keyframes([
        style({
          opacity: 1,
        }),
        style({
          transform: 'translate3d(100%, 0, 0)',
          opacity: 0,
        }),
      ]))),
    ]),
  ],
  preserveWhitespaces: false,
})
export class ToastrDialogComponent extends Toast {

  // constructor is only necessary when not using AoT
  constructor(
    protected toastrService: ToastrService,
    public toastPackage: ToastPackage,
  ) {
    super(toastrService, toastPackage);
  }

  action(event: Event) {
    event.stopPropagation();
    this.toastPackage.triggerAction();
    return false;
  }
}
