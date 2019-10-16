import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MenuComponent } from './menu.component';
import { CollapseModule } from 'ngx-bootstrap';
import { CoreModule, SharedModule } from '@rero/ng-core';
import {TranslateModule} from '@ngx-translate/core';
import { HttpClientModule } from '@angular/common/http';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { UserService } from '../service/user.service';


describe('MenuComponent', () => {
  let component: MenuComponent;
  let fixture: ComponentFixture<MenuComponent>;
  const userService = jasmine.createSpyObj('UserService', ['getCurrentUser']);
  userService.getCurrentUser.and.returnValue({
    first_name: 'John',
    last_name: 'Doe'
  });

  beforeEach(async(() => {


    TestBed.configureTestingModule({
      imports: [
        CollapseModule, CoreModule, SharedModule,  TranslateModule.forRoot(),
        HttpClientModule, BrowserModule, BrowserAnimationsModule],
      declarations: [ MenuComponent ],
      providers: [
        { provide: UserService, useValue: userService }
      ]
    })
    .compileComponents();

  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MenuComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
