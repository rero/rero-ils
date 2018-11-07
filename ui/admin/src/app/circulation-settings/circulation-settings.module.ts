import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { CirculationSettingsRoutingModule } from './circulation-settings-routing.module';
import { MainComponent } from './main/main.component';

@NgModule({
  declarations: [MainComponent],
  imports: [
    CommonModule,
    CirculationSettingsRoutingModule
  ]
})
export class CirculationSettingsModule { }
