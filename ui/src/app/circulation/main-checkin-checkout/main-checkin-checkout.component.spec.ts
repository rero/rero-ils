import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MainCheckinCheckoutComponent } from './main-checkin-checkout.component';

describe('MainCheckinCheckoutComponent', () => {
  let component: MainCheckinCheckoutComponent;
  let fixture: ComponentFixture<MainCheckinCheckoutComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MainCheckinCheckoutComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MainCheckinCheckoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
