import { TestBed } from '@angular/core/testing';

import { PatronTypeService } from './patron-type.service';

describe('PatronTypeService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: PatronTypeService = TestBed.get(PatronTypeService);
    expect(service).toBeTruthy();
  });
});
