import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { UserService } from '../user.service';

@Component({
  selector: 'libraries-mylibrary',
  template: ``,
  styles: []
})
export class MylibraryComponent implements OnInit {

  constructor(
    private router: Router,
    private currentUser: UserService
  ) {}

  ngOnInit() {
    this.currentUser.loggedUser.subscribe(user => {
      if (user) {
        this.router.navigate(['/records/libraries', user.library.pid]);
      }
    });
  }
}
