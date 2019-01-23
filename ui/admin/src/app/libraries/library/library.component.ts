import { Component, OnInit } from '@angular/core';
import { FormArray, FormGroup } from '@angular/forms';

import { LibraryFormService } from '../library-form.service';
import { LibrariesService } from '../libraries.service';
import { Library } from '../library';
import { BrowserService } from '../../browser.service';
import { UserService } from 'src/app/user.service';
import { ValidateUniqueCode } from '../validators/validate-unique-code.validator';

@Component({
  selector: 'libraries-library',
  templateUrl: './library.component.html',
  styleUrls: ['./library.component.scss']
})
export class LibraryComponent implements OnInit {

  public library: Library;

  public libForm: FormGroup;

  constructor(
    private browser: BrowserService,
    public librariesService: LibrariesService,
    public libraryForm: LibraryFormService,
    public userService: UserService
  ) { }

  ngOnInit() {
    this.userService.loggedUser.subscribe(user => {
      this.librariesService.currentLibrary.subscribe(
        library => {
          this.library = library;
          this.libraryForm.populate(library);
          this.libForm = this.libraryForm.form;
          this.libForm.controls['code'].setAsyncValidators(
            ValidateUniqueCode.createValidator(
              this.librariesService,
              user.organisation_pid,
              library.code
            )
          );
        }
      );
    });
  }

  get name() { return this.libraryForm.name; }
  get address() { return this.libraryForm.address; }
  get email() { return this.libraryForm.email; }
  get code() { return this.libraryForm.code; }
  get openingHours() { return <FormArray>this.libraryForm.opening_hours; }

  onSubmit() {
    this.libraryForm.setId(this.library.id);
    this.libraryForm.setLibraryPid(this.library.id);
    this.libraryForm.setSchema(this.library.$schema);
    this.library.update(this.libraryForm.getValues());
    this.librariesService.save(this.library);
  }

  onCancel() {
    this.browser.redirect('/libraries/' + this.library.pid);
  }

  addTime(day_index): void {
    this.libraryForm.addTime(day_index);
  }

  deleteTime(day_index, time_index): void {
    this.libraryForm.deleteTime(day_index, time_index);
  }
}
