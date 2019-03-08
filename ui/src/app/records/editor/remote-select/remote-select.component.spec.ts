import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { RemoteSelectComponent } from './remote-select.component';

describe('RemoteSelectComponent', () => {
  let component: RemoteSelectComponent;
  let fixture: ComponentFixture<RemoteSelectComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ RemoteSelectComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(RemoteSelectComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
