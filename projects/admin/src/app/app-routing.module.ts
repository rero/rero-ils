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
import { Routes, RouterModule, UrlSegment } from '@angular/router';
import { FrontpageComponent } from './frontpage/frontpage.component';
import { RecordSearchComponent, EditorComponent, DetailComponent } from '@rero/ng-core';
import { ItemTypesBriefViewComponent } from './record/brief-view/item-types-brief-view.component';
import { CircPoliciesBriefViewComponent } from './record/brief-view/circ-policies-brief-view.component';
import { DocumentsBriefViewComponent } from './record/brief-view/documents-brief-view.component';
import { LibrariesBriefViewComponent } from './record/brief-view/libraries-brief-view.component';
import { PatronTypesBriefViewComponent } from './record/brief-view/patron-types-brief-view.component';
import { PatronsBriefViewComponent } from './record/brief-view/patrons-brief-view.component';
import { PersonsBriefViewComponent } from './record/brief-view/persons-brief-view.component';
import { LibraryComponent } from './record/custom-editor/libraries/library.component';
import { CirculationPolicyComponent } from './record/custom-editor/circulation-settings/circulation-policy/circulation-policy.component';

export function matchedUrl(url: UrlSegment[]) {
  const segments = [
    new UrlSegment(url[0].path, {}),
    new UrlSegment(url[1].path, {})
  ];

  return {
    consumed: segments,
    posParams: { type: new UrlSegment(url[1].path, {}) }
  };
}

const cantDelete = record => false;
const cantUpdate =  record => false;
const cantAdd =  record => false;

const routes: Routes = [

  {
    path: '',
    component: FrontpageComponent
  }, {
    matcher: (url) => {
      if (url[0].path === 'records' && url[1].path === 'documents') {
        return matchedUrl(url);
      }
      return null;
    },
    children: [
      { path: '', component: RecordSearchComponent },
      { path: 'detail/:pid', component: DetailComponent },
      { path: 'edit/:pid', component: EditorComponent },
      { path: 'new', component: EditorComponent }
    ],
    data: {
      linkPrefix: 'records',
      types: [
        {
          key: 'documents',
          label: 'Documents',
          component: DocumentsBriefViewComponent
        }
      ]
    }
  }, {
      matcher: (url) => {
        if (url[0].path === 'records' && url[1].path === 'libraries') {
          return matchedUrl(url);
        }
        return null;
      },
      children: [
        { path: '', component: RecordSearchComponent },
        { path: 'detail/:pid', component: DetailComponent },
        { path: 'edit/:pid', component: LibraryComponent },
        { path: 'new', component: LibraryComponent }
      ],
      data: {
        linkPrefix: 'records',
        types: [
          {
            key: 'libraries',
            label: 'Libraries',
            component: LibrariesBriefViewComponent
          }
        ]
      }
    }, {
      matcher: (url) => {
        if (url[0].path === 'records' && url[1].path === 'patrons') {
          return matchedUrl(url);
        }
        return null;
      },
      children: [
        { path: '', component: RecordSearchComponent },
        { path: 'detail/:pid', component: DetailComponent },
        { path: 'edit/:pid', component: EditorComponent },
        { path: 'new', component: EditorComponent }
      ],
      data: {
        linkPrefix: 'records',
        types: [
          {
            key: 'patrons',
            label: 'Patrons',
            component: PatronsBriefViewComponent
          }
        ]
      }
    }, {
      matcher: (url) => {
        if (url[0].path === 'records' && url[1].path === 'persons') {
          return matchedUrl(url);
        }
        return null;
      },
      children: [
        { path: '', component: RecordSearchComponent },
        { path: 'detail/:pid', component: DetailComponent },
        { path: 'edit/:pid', component: EditorComponent },
        { path: 'new', component: EditorComponent }
      ],
      data: {
        linkPrefix: 'records',
        types: [
          {
            key: 'persons',
            label: 'Persons',
            component: PersonsBriefViewComponent,
            canDelete: cantDelete,
            canAdd: cantAdd,
            canUpdate: cantUpdate
          }
        ]
      }
    }, {
      matcher: (url) => {
        if (url[0].path === 'records' && url[1].path === 'item_types') {
          return matchedUrl(url);
        }
        return null;
      },
      children: [
        { path: '', component: RecordSearchComponent },
        { path: 'detail/:pid', component: DetailComponent },
        { path: 'edit/:pid', component: EditorComponent },
        { path: 'new', component: EditorComponent }
      ],
      data: {
        linkPrefix: 'records',
        types: [
          {
            key: 'item_types',
            label: 'Item Types',
            component: ItemTypesBriefViewComponent
          }
        ]
      }
    }, {
      matcher: (url) => {
        if (url[0].path === 'records' && url[1].path === 'patron_types') {
          return matchedUrl(url);
        }
        return null;
      },
      children: [
        { path: '', component: RecordSearchComponent },
        { path: 'detail/:pid', component: DetailComponent },
        { path: 'edit/:pid', component: EditorComponent },
        { path: 'new', component: EditorComponent }
      ],
      data: {
        linkPrefix: 'records',
        types: [
          {
            key: 'patron_types',
            label: 'Patron Types',
            component: PatronTypesBriefViewComponent
          }
        ]
      }
    }, {
      matcher: (url) => {
        if (url[0].path === 'records' && url[1].path === 'circ_policies') {
          return matchedUrl(url);
        }
        return null;
      },
      children: [
        { path: '', component: RecordSearchComponent },
        { path: 'detail/:pid', component: DetailComponent },
        { path: 'edit/:pid', component: CirculationPolicyComponent },
        { path: 'new', component: CirculationPolicyComponent }
      ],
      data: {
        linkPrefix: 'records',
        types: [
          {
            key: 'circ_policies',
            label: 'Circulation Policies',
            component: CircPoliciesBriefViewComponent
          }
        ]
      }
    }

//   {
//     path: '',
//     component: FrontpageComponent
//   }, {
//     path: 'records',
//     children: [
//       { path: ':type', component: RecordSearchComponent },
//       { path: ':type/detail/:pid', component: DetailComponent },
//       { path: ':type/edit/:pid', component: EditorComponent },
//       { path: ':type/new', component: EditorComponent }
//     ],
//     data: {
//       linkPrefix: '/records',
//       types: [
//         {
//           key: 'documents',
//           label: 'Documents',
//           component: DocumentsBriefViewComponent
//         },
//         {
//           key: 'libraries',
//           label: 'Libraries',
//           component: LibrariesBriefViewComponent
//         },
//         {
//           key: 'patrons',
//           label: 'Patrons',
//           component: PatronsBriefViewComponent
//         },
//         {
//           key: 'persons',
//           label: 'Persons',
//           component: PersonsBriefViewComponent
//         },
//         {
//           key: 'item_types',
//           label: 'Items Types',
//           component: ItemTypesBriefViewComponent
//         },
//         {
//           key: 'patron_types',
//           label: 'Patron Types',
//           component: PatronTypesBriefViewComponent
//         },
//         {
//           key: 'circ_policies',
//           label: 'Circ Policies',
//           component: CircPoliciesBriefViewComponent
//         }
//       ]
//     }
//   }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
