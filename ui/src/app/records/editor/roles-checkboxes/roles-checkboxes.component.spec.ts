import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RolesCheckboxesComponent } from './roles-checkboxes.component';

describe('RolesCheckboxesComponent', () => {
  let component: RolesCheckboxesComponent;
  let fixture: ComponentFixture<RolesCheckboxesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RolesCheckboxesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RolesCheckboxesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
