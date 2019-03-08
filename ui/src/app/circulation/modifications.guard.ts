import { Injectable } from '@angular/core';
import { CanDeactivate, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { Observable } from 'rxjs';
import { NoPendingChange } from './main-checkin-checkout/main-checkin-checkout.component';

@Injectable({
  providedIn: 'root'
})
export class ModificationsGuard implements CanDeactivate<NoPendingChange> {
  canDeactivate(
    component: NoPendingChange,
    next: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): Observable<boolean> | Promise<boolean> | boolean {
    return component.noPendingChange();
  }
}
