import { TestBed } from '@angular/core/testing';

import { LibraryFormService } from './library-form.service';

describe('LibraryFormService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: LibraryFormService = TestBed.get(LibraryFormService);
    expect(service).toBeTruthy();
  });
});
