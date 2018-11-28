import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { CirculationRoutingModule } from './circulation-routing.module';
import { MainComponent } from './main/main.component';
import { MainRequestComponent } from './main-request/main-request.component';
import { MainCheckinCheckoutComponent } from './main-checkin-checkout/main-checkin-checkout.component';
import { TranslateModule } from '@ngx-translate/core';
import { SharedModule } from '../shared.module';
import { RequestedLoansListComponent } from './requested-loans-list/requested-loans-list.component';
import { PatronDetailedComponent } from './patron-detailed/patron-detailed.component';
import { LoansListComponent } from './loans-list/loans-list.component';

@NgModule({
  declarations: [
    MainComponent,
    MainRequestComponent,
    MainCheckinCheckoutComponent,
    RequestedLoansListComponent,
    PatronDetailedComponent,
    LoansListComponent
  ],
  imports: [
    CommonModule,
    CirculationRoutingModule,
    SharedModule
  ]
})
export class CirculationModule { }
