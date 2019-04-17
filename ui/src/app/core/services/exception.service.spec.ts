import { TestBed } from '@angular/core/testing';

import { ExceptionService } from './exception.service';

describe('ExceptionService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ExceptionService = TestBed.get(ExceptionService);
    expect(service).toBeTruthy();
  });
});
