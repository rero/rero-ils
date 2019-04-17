import { TestBed } from '@angular/core/testing';

import { ResponseStatusService } from './response-status.service';

describe('ResponseStatusService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ResponseStatusService = TestBed.get(ResponseStatusService);
    expect(service).toBeTruthy();
  });
});
