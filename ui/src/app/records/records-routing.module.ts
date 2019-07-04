/*

RERO ILS
Copyright (C) 2019 RERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

*/

import { NgModule } from '@angular/core';
import { Routes, RouterModule } from '@angular/router';
import { AdminSearchComponent } from './search/admin-search/admin-search.component';
import { PublicSearchComponent } from './search/public-search/public-search.component';
import { EditorComponent } from './editor/editor.component';
import { CirculationPolicyComponent } from './custom-editor/circulation-settings/circulation-policy/circulation-policy.component';
import { LibraryComponent } from './custom-editor/libraries/library.component';
import { DocumentsSearchComponent } from './search/public-search/documents-search.component';
import { PersonsSearchComponent } from './search/public-search/persons-search.component';

const routes: Routes = [
  {
    path: ':viewcode/search',
    component: PublicSearchComponent,
    children: [
      {
        path: '',
        redirectTo: 'documents',
        pathMatch: 'full'
      }, {
        path: 'documents',
        component: DocumentsSearchComponent
      }, {
        path: 'persons',
        component: PersonsSearchComponent
      }
    ]
  }, {
    path: 'records/circ_policies/new',
    component: CirculationPolicyComponent
  },
  {
    path: 'records/circ_policies/:pid',
    component: CirculationPolicyComponent
  },
  {
    path: 'records/libraries/new',
    component: LibraryComponent
  },
  {
    path: 'records/libraries/:pid',
    component: LibraryComponent
  },
  {
    path: 'records/:recordType/new',
    component: EditorComponent
  },
  {
    path: 'records/:recordType/:pid',
    component: EditorComponent
  }, {
    path: 'records/:recordType',
    component: AdminSearchComponent
  }
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class RecordsRoutingModule { }
