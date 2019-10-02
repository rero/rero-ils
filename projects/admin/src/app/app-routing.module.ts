/*
 * RERO ILS UI
 * Copyright (C) 2019 RERO
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { FrontpageComponent } from './frontpage/frontpage.component';
import { RecordSearchComponent, EditorComponent, DetailComponent } from '@rero/ng-core';

const routes: Routes = [
  {
    path: '',
    component: FrontpageComponent
  }, {
    path: 'records',
    children: [
      { path: ':type', component: RecordSearchComponent },
      { path: ':type/detail/:pid', component: DetailComponent },
      { path: ':type/edit/:pid', component: EditorComponent },
      { path: ':type/new', component: EditorComponent }
    ],
    data: {
      linkPrefix: '/records',
      types: [
        {
          key: 'documents',
          label: 'Documents',
          // component: DocumentComponent,
          // detailComponent: DetailComponent
        },
        {
          key: 'libraries',
          label: 'Libraries',
          // component: InstitutionComponent
        },
        {
          key: 'patrons',
          label: 'Patrons'
        },
        {
          key: 'persons',
          label: 'Persons'
        },
        {
          key: 'item_types',
          label: 'Items Types'
        },
        {
          key: 'patron_types',
          label: 'Patron Types'
        },
        {
          key: 'circ_policies',
          label: 'Circ Policies'
        }
      ]
    }
  }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
