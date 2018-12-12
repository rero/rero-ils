import { Component, OnInit } from '@angular/core';
import { FormArray, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

import { cleanDictKeys } from '@app/core';
import { UniqueValidator } from '@app/core';
import { LibraryFormService } from './library-form.service';
import { Library } from './library';
import { UserService } from 'src/app/user.service';
import { RecordsService } from '../../records.service';
import { ApiService } from '@app/core';

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
    private apiService: ApiService
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
        this.router.navigate(['/records', 'libraries']);
      });
    } else {
      const organisation = {
        $ref: this.apiService.getApiEntryPointByType('organisations', true) + this.organisationPid
      };
      this.library.organisation = organisation;
      this.recordsService.create('libraries', cleanDictKeys(this.library)).subscribe(record => {
        this.router.navigate(['/records', 'libraries']);
      });
    }
  }

  onCancel() {
    this.router.navigate(['/records', 'libraries']);
  }

  addTime(day_index): void {
    this.libraryForm.addTime(day_index);
  }

  deleteTime(day_index, time_index): void {
    this.libraryForm.deleteTime(day_index, time_index);
  }
}
