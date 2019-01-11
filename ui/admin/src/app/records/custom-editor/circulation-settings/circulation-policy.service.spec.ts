import { TestBed } from '@angular/core/testing';

import { CirculationPolicyService } from './circulation-policy.service';

describe('CirculationPolicyService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: CirculationPolicyService = TestBed.get(CirculationPolicyService);
    expect(service).toBeTruthy();
  });
});
