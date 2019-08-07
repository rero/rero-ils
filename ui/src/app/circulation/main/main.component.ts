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

import { Component, OnInit } from '@angular/core';
import { UserService } from '../../user.service';

@Component({
  selector: 'app-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss']
})
export class MainComponent implements OnInit {

  public loading = true;
  public permission_denied = true;
  public loggedUser;
  constructor(private userService: UserService) { }

  ngOnInit() {
    this.userService.loggedUser.subscribe(user => {
      if (user) {
        if (user.roles.some(role => role === 'librarian')) {
          this.permission_denied = false;
        }
        this.loading = false;
        this.loggedUser = user;
      }
    });
  }
}
