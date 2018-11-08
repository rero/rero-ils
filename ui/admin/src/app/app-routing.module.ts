import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { MylibraryComponent } from './mylibrary/mylibrary.component';

const routes: Routes = [
  {
    path: 'mylibrary',
    component: MylibraryComponent
  },
  {
    path: 'libraries',
    loadChildren: './libraries/libraries.module#LibrariesModule'
  }, {
    path: 'circulation_settings',
    loadChildren: './circulation-settings/circulation-settings.module#CirculationSettingsModule'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
