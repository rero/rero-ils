import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { LibrarySettingsRoutingModule } from './library-settings-routing.module';
import { MainComponent } from './main/main.component';

@NgModule({
  declarations: [MainComponent],
  imports: [
    CommonModule,
    LibrarySettingsRoutingModule
  ]
})
export class LibrarySettingsModule { }
