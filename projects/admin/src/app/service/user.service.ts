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

import { Injectable, EventEmitter } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { User } from '../class/User';
import { AppConfigService } from './app-config.service';

@Injectable({
  providedIn: 'root'
})
export class UserService {

  readonly onUserLoaded: EventEmitter<User> = new EventEmitter();

  private user: User;

  constructor(
    private http: HttpClient,
    private appConfigService: AppConfigService
  ) { }

  getCurrentUser() {
    return this.user;
  }

  public loadLoggedUser() {
    this.http.get<any>('/patrons/logged_user?resolve').subscribe(data => {
      let user = null;
      if (data.metadata) {
        user = new User(data.metadata);
        user.is_logged = true;
      } else {
        user = new User({});
      }
      this.appConfigService.setSettings(data.settings);
      this.user = user;
      this.onUserLoaded.emit(user);
    });
  }
}
