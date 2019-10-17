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

import { Component, OnInit } from '@angular/core';
import { UserService } from './service/user.service';
import { User } from './class/user';
import { AppConfigService } from './service/app-config.service';
import { TranslateService } from '@rero/ng-core';

@Component({
  selector: 'admin-root',
  templateUrl: './app.component.html'
})
export class AppComponent implements OnInit {

  user: any;

  access = false;

  constructor(
    private userService: UserService,
    private appConfigService: AppConfigService,
    private translateService: TranslateService
    ) { }

  ngOnInit() {
    this.userService.loadLoggedUser();
    this.userService.onUserLoaded.subscribe((logged: User) => {
      // User not logged
      if (!logged) {
        throw new Error('User is not logged');
      }
      const language = this.appConfigService.getSettings().language;
      if (language) {
        this.translateService.setLanguage(language);
      } else {
        const browserLang = this.translateService.getBrowserLang();
        this.translateService.setLanguage(
          browserLang.match(this.appConfigService.languages.join('|')) ?
          browserLang : this.appConfigService.defaultLanguage
        );
      }
      const user = this.userService.getCurrentUser();

      this.access = user.isAuthorizedAdminAccess(
        this.appConfigService.adminRoles
      );
      this.user = user;
    });
  }
}
