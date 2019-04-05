import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ToastrDialogComponent } from './toastr-dialog.component';

describe('ToastrDialogComponent', () => {
  let component: ToastrDialogComponent;
  let fixture: ComponentFixture<ToastrDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ToastrDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ToastrDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
