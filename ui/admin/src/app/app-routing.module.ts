import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';

const routes: Routes = [
  {
    path: 'library_settings',
    loadChildren: './library-settings/library-settings.module#LibrarySettingsModule'
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
