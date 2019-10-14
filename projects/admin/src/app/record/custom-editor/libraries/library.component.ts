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
import { FormArray, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService, UniqueValidator, cleanDictKeys, RecordService } from '@rero/ng-core';
import { LibraryFormService } from './library-form.service';
import { Library } from './library';
import { ToastrService } from 'ngx-toastr';
import { UserService } from '../../../service/user.service';
import { marker as _ } from '@biesbjerg/ngx-translate-extract-marker';

@Component({
  selector: 'admin-libraries-library',
  templateUrl: './library.component.html',
  styleUrls: ['./library.component.scss']
})
export class LibraryComponent implements OnInit {

  public library: Library;
  public libForm: FormGroup;
  public organisationPid;

  constructor(
    private recordService: RecordService,
    private libraryForm: LibraryFormService,
    private route: ActivatedRoute,
    private router: Router,
    private userService: UserService,
    private apiService: ApiService,
    private toastService: ToastrService
  ) { }

  ngOnInit() {
    this.libForm = this.libraryForm.form;
    this.route.params.subscribe( (params) => {
      const loggedUser = this.userService.getCurrentUser();
      if (loggedUser) {
        this.organisationPid = loggedUser.library.organisation.pid;
      }
      if (params && params.pid) {
        this.recordService.getRecord('libraries', params.pid, 1).subscribe(record => {
          this.library = new Library(record.metadata);
          this.libraryForm.populate(record.metadata);
          this.setAsyncValidator();
        });
      } else {
        this.library = new Library({});
        this.setAsyncValidator();
      }
    });
  }

  setAsyncValidator() {
    this.libForm.controls.code.setAsyncValidators([
      UniqueValidator.createValidator(
        this.recordService,
        'libraries',
        'code',
        this.library.pid
      )
    ]);
  }

  get name() { return this.libraryForm.name; }
  get address() { return this.libraryForm.address; }
  get email() { return this.libraryForm.email; }
  get code() { return this.libraryForm.code; }
  get openingHours() { return this.libraryForm.opening_hours as FormArray; }

  onSubmit() {
    this.library.update(this.libraryForm.getValues());
    if (this.library.pid) {
      this.recordService.update('libraries', cleanDictKeys(this.library)).subscribe(record => {
        this.toastService.success(
          _('Record Updated!'),
          _('libraries')
        );
        this.router.navigate(['/records', 'libraries']);
      });
    } else {
      const organisation = {
        $ref: this.apiService.getEndpointByType('organisations', true) + this.organisationPid
      };
      this.library.organisation = organisation;
      this.recordService.create('libraries', cleanDictKeys(this.library)).subscribe(record => {
        this.toastService.success(
          _('Record created!'),
          _('libraries')
        );
        this.router.navigate(['/records', 'libraries']);
      });
    }
    this.libraryForm.reset();
  }

  onCancel() {
    this.router.navigate(['/records', 'libraries']);
    this.libraryForm.reset();
  }
  addTime(dayIndex): void {
    this.libraryForm.addTime(dayIndex);
  }

  deleteTime(dayIndex, timeIndex): void {
    this.libraryForm.deleteTime(dayIndex, timeIndex);
  }
}
