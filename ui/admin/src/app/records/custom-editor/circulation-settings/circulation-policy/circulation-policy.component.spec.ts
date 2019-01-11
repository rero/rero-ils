import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CirculationPolicyComponent } from './circulation-policy.component';

describe('CirculationPolicyComponent', () => {
  let component: CirculationPolicyComponent;
  let fixture: ComponentFixture<CirculationPolicyComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CirculationPolicyComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CirculationPolicyComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
