import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LoansListComponent } from './loans-list.component';

describe('LoansListComponent', () => {
  let component: LoansListComponent;
  let fixture: ComponentFixture<LoansListComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ LoansListComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LoansListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
