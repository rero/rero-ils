import { Injectable } from '@angular/core';
import { Bootstrap4FrameworkComponent } from './bootstrap4-framework.component';
// import { Framework } from 'angular6-json-schema-form';

// Bootstrap 4 Framework
// https://github.com/ng-bootstrap/ng-bootstrap

@Injectable({
    providedIn: 'root'
})
// export class Bootstrap4Framework implements Framework {
export class CustomBootstrap4Framework {
  name = 'rero';

  framework = Bootstrap4FrameworkComponent;

  stylesheets = [
    '//stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css'
  ];

  scripts = [
    '//code.jquery.com/jquery-3.3.1.slim.min.js',
    '//cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js',
    '//stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js',
  ];
}
