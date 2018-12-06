import { Injectable } from '@angular/core';
import { AsyncValidator, AbstractControl, ValidationErrors } from '@angular/forms';
import { catchError, map } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { LibrariesService } from '../libraries/libraries.service';

@Injectable({ providedIn: 'root' })
export class LibraryCodeUniqueValidator implements AsyncValidator {
  constructor(private librariesService: LibrariesService) {}

  validate(
      control: AbstractControl
  ): Promise<ValidationErrors | null> | Observable<ValidationErrors | null> {
      return this.librariesService.checkIfCodeAlreadyTaken(control.value).pipe(
        map(isTaken => (isTaken ? { isTaken: true } : null)),
        catchError(() => null)
      );
  }
}
