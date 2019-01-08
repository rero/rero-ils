import { TestBed } from '@angular/core/testing';

import { LibraryExceptionFormService } from './library-exception-form.service';

describe('LibraryExceptionFormService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: LibraryExceptionFormService = TestBed.get(LibraryExceptionFormService);
    expect(service).toBeTruthy();
  });
});
