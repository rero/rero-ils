import { Component } from '@angular/core';
import { FormArray, FormGroup } from '@angular/forms';

import { LibraryFormService } from '../library-form.service';
import { LibrariesService } from '../libraries.service';
import { Library } from '../library';
import { BrowserService } from '../../browser.service';

@Component({
  selector: 'libraries-library',
  templateUrl: './library.component.html',
  styleUrls: ['./library.component.scss']
})
export class LibraryComponent {

  public library: Library;

  public libForm: FormGroup;

  constructor(
    private browser: BrowserService,
    public librariesService: LibrariesService,
    public libraryForm: LibraryFormService
  ) {
    this.librariesService.currentLibrary.subscribe(
      library => {
        this.library = library;
        this.libraryForm.populate(library);
        this.libForm = this.libraryForm.form;
      }
    );
  }

  get name() { return this.libraryForm.name; }
  get address() { return this.libraryForm.address; }
  get email() { return this.libraryForm.email; }
  get openingHours() { return <FormArray>this.libraryForm.opening_hours; }

  onSubmit() {
    this.libraryForm.setId(this.library.id);
    this.libraryForm.setLibraryPid(this.library.id);
    this.libraryForm.setSchema(this.library.$schema);
    this.library.update(this.libraryForm.getValues());
    this.librariesService.save(this.library, '/libraries/' + this.library.pid);
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
