import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class AlertsService {

  alert = new BehaviorSubject(null);

  addAlert(type, message) {
    this.alert.next({
      type: type,
      message: message
    });
  }

}
