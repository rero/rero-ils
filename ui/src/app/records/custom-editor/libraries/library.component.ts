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
import { FormArray, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { combineLatest } from 'rxjs';
import { ApiService, UniqueValidator, cleanDictKeys, _ } from '@app/core';
import { LibraryFormService } from './library-form.service';
import { Library } from './library';
import { UserService } from 'src/app/user.service';
import { RecordsService } from '../../records.service';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'libraries-library',
  templateUrl: './library.component.html',
  styleUrls: ['./library.component.scss']
})
export class LibraryComponent implements OnInit {

  public library: Library;
  public libForm: FormGroup;
  public organisationPid;

  constructor(
    private recordsService: RecordsService,
    private libraryForm: LibraryFormService,
    private route: ActivatedRoute,
    private router: Router,
    private userService: UserService,
    private apiService: ApiService,
    private toastService: ToastrService
  ) { }

  ngOnInit() {
    this.libForm = this.libraryForm.form;
    combineLatest(this.userService.loggedUser, this.route.params)
    .subscribe(([loggedUser, params]) => {
      if (loggedUser) {
        this.organisationPid = loggedUser.library.organisation.pid;
      }
      if (params && params.pid) {
        this.recordsService.getRecord('libraries', params.pid, 1).subscribe(record => {
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
    this.libForm.controls['code'].setAsyncValidators([
      UniqueValidator.createValidator(
        this.recordsService,
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
  get openingHours() { return <FormArray>this.libraryForm.opening_hours; }

  onSubmit() {
    this.library.update(this.libraryForm.getValues());
    if (this.library.pid) {
      this.recordsService.update('libraries', cleanDictKeys(this.library)).subscribe(record => {
        this.toastService.success(
          _('Record Updated!'),
          _('libraries')
        );
        this.router.navigate(['/records', 'libraries']);
      });
    } else {
      const organisation = {
        $ref: this.apiService.getApiEntryPointByType('organisations', true) + this.organisationPid
      };
      this.library.organisation = organisation;
      this.recordsService.create('libraries', cleanDictKeys(this.library)).subscribe(record => {
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

  addTime(day_index): void {
    this.libraryForm.addTime(day_index);
  }

  deleteTime(day_index, time_index): void {
    this.libraryForm.deleteTime(day_index, time_index);
  }
}
