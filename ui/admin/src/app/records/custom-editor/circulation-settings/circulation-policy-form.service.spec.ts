import { TestBed } from '@angular/core/testing';

import { CirculationPolicyFormService } from './circulation-policy-form.service';

describe('CirculationPolicyFormService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: CirculationPolicyFormService = TestBed.get(CirculationPolicyFormService);
    expect(service).toBeTruthy();
  });
});
