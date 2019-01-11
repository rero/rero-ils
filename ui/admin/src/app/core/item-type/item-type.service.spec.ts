import { TestBed } from '@angular/core/testing';

import { ItemTypeService } from './item-type.service';

describe('ItemTypeService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ItemTypeService = TestBed.get(ItemTypeService);
    expect(service).toBeTruthy();
  });
});
