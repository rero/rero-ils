import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { SearchComponent } from './search/search.component';
import { EditorComponent } from './editor/editor.component';

const routes: Routes = [
  {
    path: ':recordType/new',
    component: EditorComponent
  },
  {
    path: ':recordType/:pid',
    component: EditorComponent
  },
  {
    path: ':recordType',
    component: SearchComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class RecordsRoutingModule { }
