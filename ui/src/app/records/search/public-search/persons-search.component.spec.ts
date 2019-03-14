import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PersonsSearchComponent } from './persons-search.component';

describe('PersonsSearchComponent', () => {
  let component: PersonsSearchComponent;
  let fixture: ComponentFixture<PersonsSearchComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PersonsSearchComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PersonsSearchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
