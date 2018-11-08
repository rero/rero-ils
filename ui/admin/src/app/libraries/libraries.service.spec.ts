import { TestBed } from '@angular/core/testing';

import { LibrariesService } from './libraries.service';

describe('LibrariesService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: LibrariesService = TestBed.get(LibrariesService);
    expect(service).toBeTruthy();
  });
});
