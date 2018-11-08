import { TestBed } from '@angular/core/testing';

import { InMemoryLibrariesDataService } from './in-memory-libraries-data.service';

describe('InMemoryLibrariesDataService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: InMemoryLibrariesDataService = TestBed.get(InMemoryLibrariesDataService);
    expect(service).toBeTruthy();
  });
});
