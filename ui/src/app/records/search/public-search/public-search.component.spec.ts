import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PublicSearchComponent } from './public-search.component';

describe('PublicSearchComponent', () => {
  let component: PublicSearchComponent;
  let fixture: ComponentFixture<PublicSearchComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PublicSearchComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PublicSearchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
