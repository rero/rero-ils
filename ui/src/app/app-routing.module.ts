import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { MylibraryComponent } from './mylibrary/mylibrary.component';
import { PageNotFoundComponent } from './page-not-found/page-not-found.component';
import { ExceptionComponent } from './core';

const routes: Routes = [
  {
    path: 'mylibrary',
    component: MylibraryComponent
  },
  {
    path: 'circulation',
    loadChildren: './circulation/circulation.module#CirculationModule'
  },
  {
    path: 'exception',
    component: ExceptionComponent,
    pathMatch: 'full'
  },
  {
    path: '',
    loadChildren: './records/records.module#RecordsModule'
  },
  {
    path: '**',
    component: PageNotFoundComponent
  }
];

@NgModule({
  imports: [RouterModule.forRoot(
    routes
  )],
  exports: [RouterModule]
})
export class AppRoutingModule { }
