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

import { Component, OnInit, Injector } from '@angular/core';
import { User } from './users';
import { UserService } from './user.service';
import { TranslateService } from '@ngx-translate/core';
import * as moment from 'moment';
import { ApiService } from './core';
import { createCustomElement } from '@angular/elements';
import { AutocompleteComponent } from './autocomplete/autocomplete.component';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {

  loggedUser: User;

  constructor(
    private userService: UserService,
    private translate: TranslateService,
    private apiService: ApiService,
    private injector: Injector
    ) {
      const autoElement = createCustomElement(
        AutocompleteComponent,
        { injector: this.injector }
      );
      customElements.define('search-autocomplete', autoElement);
    }

  ngOnInit() {
    this.userService.userSettings.subscribe(settings => {
      if (settings) {
        moment.locale(settings.language);
        this.translate.use(settings.language);
        this.apiService.setBaseUrl(settings.baseUrl);
      }
    });
  }
}
