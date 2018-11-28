import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MainRequestComponent } from './main-request.component';

describe('MainRequestComponent', () => {
  let component: MainRequestComponent;
  let fixture: ComponentFixture<MainRequestComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MainRequestComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MainRequestComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
