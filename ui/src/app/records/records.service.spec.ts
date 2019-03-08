import { TestBed } from '@angular/core/testing';

import { RecordsService } from './records.service';

describe('RecordsService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: RecordsService = TestBed.get(RecordsService);
    expect(service).toBeTruthy();
  });
});
