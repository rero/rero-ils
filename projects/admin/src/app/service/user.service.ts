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
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { User } from '../class/User';

@Injectable({
  providedIn: 'root'
})
export class UserService {

  private user: User;

  constructor(
    private http: HttpClient
  ) { }

  getLoggedUser() {
    return this.http.get<any>('/patrons/logged_user?resolve');
  }

  getCurrentUser() {
    return this.user;
  }

  setCurrentUser(user: any) {
    this.user = user;
  }
}
