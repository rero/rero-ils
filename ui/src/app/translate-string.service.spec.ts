import { TestBed } from '@angular/core/testing';

import { TranslateStringService } from './translate-string.service';

describe('TranslateStringService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: TranslateStringService = TestBed.get(TranslateStringService);
    expect(service).toBeTruthy();
  });
});
