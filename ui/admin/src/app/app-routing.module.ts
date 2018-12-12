import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { MylibraryComponent } from './mylibrary/mylibrary.component';

const routes: Routes = [
  {
    path: 'mylibrary',
    component: MylibraryComponent
  },
  {
    path: 'circulation',
    loadChildren: './circulation/circulation.module#CirculationModule'
  }, {
    path: 'records',
    loadChildren: './records/records.module#RecordsModule'
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
