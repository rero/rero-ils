import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MylibraryComponent } from './mylibrary.component';

describe('MylibraryComponent', () => {
  let component: MylibraryComponent;
  let fixture: ComponentFixture<MylibraryComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MylibraryComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MylibraryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
