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
import { RecordSearchComponent, DetailComponent } from '@rero/ng-core';
import { DocumentBriefComponent } from './document-brief/document-brief.component';

const routes: Routes = [
  {
    path: 'global/search',
    children: [
      { path: ':type', component: RecordSearchComponent },
      { path: ':type/detail/:pid', component: DetailComponent }
    ],
    data: {
      showSearchInput: true,
      adminMode: false,
      linkPrefix: '/global/search',
      detailUrl: '/global/:type/:pid',
      types: [
        {
          key: 'documents',
          component: DocumentBriefComponent,
          label: 'Documents'
        }
      ]
    }
  }, {
    path: 'highlands/search',
    children: [
      { path: ':type', component: RecordSearchComponent },
      { path: ':type/detail/:pid', component: DetailComponent }
    ],
    data: {
      showSearchInput: true,
      adminMode: false,
      linkPrefix: '/highlands/search',
      detailUrl: '/highlands/:type/:pid',
      types: [
        {
          key: 'documents',
          component: DocumentBriefComponent,
          label: 'Documents',
          preFilters: {
            view: 'highlands'
          }
        }
      ]
    }
  }, {
    path: 'aoste/search',
    children: [
      { path: ':type', component: RecordSearchComponent },
      { path: ':type/detail/:pid', component: DetailComponent }
    ],
    data: {
      showSearchInput: true,
      adminMode: false,
      linkPrefix: '/aoste/search',
      detailUrl: '/aoste/:type/:pid',
      types: [
        {
          key: 'documents',
          label: 'Documents',
          component: DocumentBriefComponent,
          preFilters: {
            view: 'aoste'
          }
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
