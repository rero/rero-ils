import { TestBed } from '@angular/core/testing';

import { OrganisationViewService } from './organisation-view.service';

describe('OrganisationViewService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: OrganisationViewService = TestBed.get(OrganisationViewService);
    expect(service).toBeTruthy();
  });
});
