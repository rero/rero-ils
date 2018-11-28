import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ExceptionDatesEditComponent } from './exception-dates-edit.component';

describe('ExceptionDatesEditComponent', () => {
  let component: ExceptionDatesEditComponent;
  let fixture: ComponentFixture<ExceptionDatesEditComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ExceptionDatesEditComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ExceptionDatesEditComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
