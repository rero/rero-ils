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
import { MylibraryComponent } from './mylibrary/mylibrary.component';

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

export function cant(record) { return false; }

export function documentsMatcher(url) {
  if (url[0].path === 'records' && url[1].path === 'documents') {
    return matchedUrl(url);
  }
  return null;
}

export function librariesMatcher(url) {
  if (url[0].path === 'records' && url[1].path === 'libraries') {
    return matchedUrl(url);
  }
  return null;
}

export function locationsMatcher(url) {
  if (url[0].path === 'records' && url[1].path === 'libraries') {
    return matchedUrl(url);
  }
  return null;
}

export function itemTypesMatcher(url) {
  if (url[0].path === 'records' && url[1].path === 'item_types') {
    return matchedUrl(url);
  }
  return null;
}

export function itemsMatcher(url) {
  if (url[0].path === 'records' && url[1].path === 'items') {
    return matchedUrl(url);
  }
  return null;
}

export function patronTypesMatcher(url) {
  if (url[0].path === 'records' && url[1].path === 'patron_types') {
    return matchedUrl(url);
  }
  return null;
}

export function patronsMatcher(url) {
  if (url[0].path === 'records' && url[1].path === 'patrons') {
    return matchedUrl(url);
  }
  return null;
}

export function personsMatcher(url) {
  if (url[0].path === 'records' && url[1].path === 'persons') {
    return matchedUrl(url);
  }
  return null;
}

export function circPoliciesMatcher(url) {
  if (url[0].path === 'records' && url[1].path === 'circ_policies') {
    return matchedUrl(url);
  }
  return null;
}

const routes: Routes = [
  {
    path: '',
    component: FrontpageComponent
  }, {
    path: 'mylibrary',
    component: MylibraryComponent
  }, {
    path: 'circulation',
    loadChildren: () => import('./circulation/circulation.module').then(m => m.CirculationModule)
  }, {
    matcher: documentsMatcher,
    // loadChildren: () => import('@rero/ng-core').then(m => m.RecordModule)
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
    matcher: librariesMatcher,
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
    matcher: patronsMatcher,
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
    matcher: personsMatcher,
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
          canDelete: cant,
          canAdd: cant,
          canUpdate: cant
        }
      ]
    }
  }, {
    matcher: itemTypesMatcher,
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
    matcher: itemsMatcher,
    children: [
      { path: 'detail/:pid', component: DetailComponent },
      { path: 'edit/:pid', component: EditorComponent },
      { path: 'new', component: EditorComponent }
    ],
    data: {
      linkPrefix: 'records',
      types: [
        {
          key: 'items',
          label: 'Items'
        }
      ]
    }
  }, {
    matcher: locationsMatcher,
    children: [
      { path: 'detail/:pid', component: DetailComponent },
      { path: 'edit/:pid', component: EditorComponent },
      { path: 'new', component: EditorComponent }
    ],
    data: {
      linkPrefix: 'records',
      types: [
        {
          key: 'locations',
          label: 'Locations'
        }
      ]
    }
  }, {
    matcher: patronTypesMatcher,
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
    matcher: circPoliciesMatcher,
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
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }
