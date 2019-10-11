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
import { Component } from '@angular/core';
import { UserService } from './service/user.service';
import { User } from './class/User';
import { AppConfigService } from './service/app-config.service';

@Component({
  selector: 'admin-root',
  templateUrl: './app.component.html'
})
export class AppComponent {

  user: any;

  constructor(
    userService: UserService,
    appSettings: AppConfigService
    ) {
    userService.getLoggedUser().subscribe(data => {
      appSettings.setSettings(data.settings);
      const currentUser = new User(data.metadata);
      console.log(currentUser, 'user', data);
      userService.setCurrentUser(currentUser);
      this.user = currentUser;
    });
  }
}
