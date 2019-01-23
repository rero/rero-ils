import { AbstractControl } from '@angular/forms';
import { LibrariesService } from '../libraries.service';
import { map } from 'rxjs/operators';

export class ValidateUniqueCode {
  static createValidator(
    librariesService: LibrariesService,
    organisationId: string,
    currentCode: string
  ) {
    return (control: AbstractControl) => {
      return librariesService.checkIfCodeAlreadyTaken(
        // TODO: Missing OrganisationId on Json schema library
        organisationId, control.value).pipe(map((res: any) => {
          return ((control.value === currentCode) || res.hits.total === 0) ?
            null : { isTaken: true };
      }));
    };
  }
}
