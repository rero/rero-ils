import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ConfirmWindowComponent } from './confirm-window.component';

describe('ConfirmWindowComponent', () => {
  let component: ConfirmWindowComponent;
  let fixture: ComponentFixture<ConfirmWindowComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ConfirmWindowComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ConfirmWindowComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
