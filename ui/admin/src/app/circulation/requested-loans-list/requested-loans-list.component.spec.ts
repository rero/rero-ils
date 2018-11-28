import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RequestedLoansListComponent } from './requested-loans-list.component';

describe('RequestedLoansListComponent', () => {
  let component: RequestedLoansListComponent;
  let fixture: ComponentFixture<RequestedLoansListComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RequestedLoansListComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RequestedLoansListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
