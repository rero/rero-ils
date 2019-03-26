import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RefAuthorityComponent } from './ref-authority.component';

describe('RefAuthorityComponent', () => {
  let component: RefAuthorityComponent;
  let fixture: ComponentFixture<RefAuthorityComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RefAuthorityComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RefAuthorityComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
