import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Subject, BehaviorSubject } from 'rxjs';

import { User } from './User';

@Injectable({
  providedIn: 'root'
})
export class UserService {

  loggedUser: Subject<User> = new BehaviorSubject<User>(null);

  constructor(private client: HttpClient) {
    this.client.get<User>('/patrons/logged_user')
      .subscribe(user => {
        this.loggedUser.next(new User(user));
      });
  }
}
