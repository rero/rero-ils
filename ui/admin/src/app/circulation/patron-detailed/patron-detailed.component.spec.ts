import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PatronDetailedComponent } from './patron-detailed.component';

describe('PatronDetailedComponent', () => {
  let component: PatronDetailedComponent;
  let fixture: ComponentFixture<PatronDetailedComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PatronDetailedComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PatronDetailedComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
