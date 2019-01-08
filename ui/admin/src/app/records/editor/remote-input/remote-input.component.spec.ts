import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RemoteInputComponent } from './remote-input.component';

describe('RemoteInputComponent', () => {
  let component: RemoteInputComponent;
  let fixture: ComponentFixture<RemoteInputComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RemoteInputComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RemoteInputComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
