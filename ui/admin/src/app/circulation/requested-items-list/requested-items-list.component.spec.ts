import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RequestedItemsListComponent } from './requested-items-list.component';

describe('RequestedItemsListComponent', () => {
  let component: RequestedItemsListComponent;
  let fixture: ComponentFixture<RequestedItemsListComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RequestedItemsListComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RequestedItemsListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
