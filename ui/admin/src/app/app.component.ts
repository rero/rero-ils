import { Component, OnInit } from '@angular/core';
import { User } from './users';
import { UserService } from './user.service';
import { TranslateService } from '@ngx-translate/core';
import * as moment from 'moment';
import { ApiService } from './core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {

  loggedUser: User;

  constructor(
    private userService: UserService,
    private translate: TranslateService,
    private apiService: ApiService
    ) {}

  ngOnInit() {
    this.userService.userSettings.subscribe(settings => {
      if (settings) {
        moment.locale(settings.language);
        this.translate.use(settings.language);
        this.apiService.setBaseUrl(settings.baseUrl);
      }
    });
  }
}
