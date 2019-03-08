import { TestBed, async, inject } from '@angular/core/testing';

import { ModificationsGuard } from './modifications.guard';

describe('ModificationsGuard', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ModificationsGuard]
    });
  });

  it('should ...', inject([ModificationsGuard], (guard: ModificationsGuard) => {
    expect(guard).toBeTruthy();
  }));
});
