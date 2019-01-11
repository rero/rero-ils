import { TestBed } from '@angular/core/testing';

import { CirculationMappingService } from './circulation-mapping.service';

describe('CirculationMappingService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: CirculationMappingService = TestBed.get(CirculationMappingService );
    expect(service).toBeTruthy();
  });
});
