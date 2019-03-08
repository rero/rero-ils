import { Injectable } from '@angular/core';
import { BsModalService } from 'ngx-bootstrap';
import { DialogComponent } from './dialog.component';

@Injectable({
  providedIn: 'root'
})
export class DialogService {

  constructor(private modalService: BsModalService) { }

  public show(config: any) {
    const bsModalRef = this.modalService.show(DialogComponent, config);
    return bsModalRef.content.onClose;
  }
}
