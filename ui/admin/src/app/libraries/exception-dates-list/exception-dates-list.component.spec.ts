import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ExceptionDatesListComponent } from './exception-dates-list.component';

describe('ExceptionDatesListComponent', () => {
  let component: ExceptionDatesListComponent;
  let fixture: ComponentFixture<ExceptionDatesListComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExceptionDatesListComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExceptionDatesListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
