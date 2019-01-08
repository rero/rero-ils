import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ExceptionDatesComponent } from './exception-dates.component';

describe('ExceptionDatesComponent', () => {
  let component: ExceptionDatesComponent;
  let fixture: ComponentFixture<ExceptionDatesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExceptionDatesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExceptionDatesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
