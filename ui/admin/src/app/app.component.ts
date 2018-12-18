import { Component, OnInit, Input } from '@angular/core';
import { UserService } from './user.service';
import { TranslateService } from '@ngx-translate/core';
import * as moment from 'moment';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {

  constructor(
    private userService: UserService,
    private translate: TranslateService
    ) {}

  ngOnInit() {
    this.userService.loggedUser.subscribe(user => {
      if (user) {
        moment.locale(user.settings.language);
        this.translate.use(user.settings.language);
      }
    });
  }
}
