import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { MainComponent } from './main/main.component';
import { MainRequestComponent } from './main-request/main-request.component';
import { MainCheckinCheckoutComponent } from './main-checkin-checkout/main-checkin-checkout.component';

const routes: Routes = [
  {
    path: '',
    component: MainComponent,
    children: [
    {
      path: '',
      redirectTo: 'checkinout',
      pathMatch: 'full'
    }, {
      path: 'requests',
      component: MainRequestComponent
    }, {
      path: 'checkinout',
      component: MainCheckinCheckoutComponent
    }
    ]
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class CirculationRoutingModule { }
