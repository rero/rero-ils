import { Component, OnInit } from '@angular/core';
import { UserService } from '../../user.service';

@Component({
  selector: 'app-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss']
})
export class MainComponent implements OnInit {

  public loading = true;
  public permission_denied = true;
  public loggedUser;
  constructor(private userService: UserService) { }

  ngOnInit() {
    this.userService.loggedUser.subscribe(user => {
      if (user) {
        if (user.roles.some(role => role === 'librarian')) {
          this.permission_denied = false;
        }
        this.loading = false;
        this.loggedUser = user;
      }
    });
  }
}
