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
import { Router } from '@angular/router';
import { UserService } from '../service/user.service';

@Component({
  selector: 'admin-libraries-mylibrary',
  template: ``,
  styles: []
})
export class MylibraryComponent implements OnInit {

  constructor(
    private router: Router,
    private currentUser: UserService
  ) {}

  ngOnInit() {
    const user = this.currentUser.getCurrentUser();
    this.router.navigate(['/records/libraries/detail', user.library.pid]);
  }
}
