/*
 * RERO ILS UI
 * Copyright (C) 2019 RERO
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
import { Component, OnInit } from '@angular/core';
import { UserService } from '../services/user.service';
import { TranslateService } from '@ngx-translate/core';
import { CoreConfigService } from '@rero/ng-core';
// import { _ } from '@rero/ng-core';

export function _(str: string) {
  return str;
}

@Component({
  selector: 'admin-menu',
  templateUrl: './menu.component.html',
  styleUrls: ['./menu.component.scss']
})
export class MenuComponent implements OnInit {
  isCollapsed = true;
  lang: string = document.documentElement.lang;
  languages: string[];

  linksMenu = {
    navCssClass: 'navbar-nav',
    entries: [
      {
        name: _('User services'),
        iconCssClass: 'fa fa-users',
        entries: [{
          name: _('Circulation'),
          routerLink: '/',
          iconCssClass: 'fa fa-exchange'
        }, {
          name: _('Patrons'),
          routerLink: '/',
          iconCssClass: 'fa fa-users'
        }]
      }, {
        name: _('Catalog'),
        iconCssClass: 'fa fa-file-o',
        entries: [{
          name: _('Documents'),
          routerLink: '/records/documents',
          iconCssClass: 'fa fa-file-o'
        }, {
          name: _('Create a bibliographic record'),
          routerLink: '/',
          iconCssClass: 'fa fa-file-o'
        }, {
          name: _('Persons'),
          routerLink: '/records/persons',
          iconCssClass: 'fa fa-user'
        }]
      }, {
        name: _('Admin & Monitoring'),
        iconCssClass: 'fa fa-cogs',
        entries: [{
          name: _('Circulation policies'),
          routerLink: '/records/circ_policies',
          iconCssClass: 'fa fa-exchange'
        }, {
          name: _('Item types'),
          routerLink: '/records/item_types',
          iconCssClass: 'fa fa-file-o'
        }, {
          name: _('Patron types'),
          routerLink: '/records/patron_types',
          iconCssClass: 'fa fa-users'
        }, {
          name: _('My Library'),
          routerLink: '/',
          iconCssClass: 'fa fa-university'
        }, {
          name: _('Libraries'),
          routerLink: '/records/libraries',
          iconCssClass: 'fa fa-university'
        }]
      }
    ]
  };

  languagesMenu = {
    navCssClass: 'navbar-nav',
    entries: [{
      name: _('Menu'),
      iconCssClass: 'fa fa-bars',
      entries: [{
        name: _('Help'),
        iconCssClass: 'fa fa-help',
        href: 'https://ils.test.rero.ch/help'
      }]
    }]
  };
  userMenu = {
    navCssClass: 'navbar-nav',
    iconCssClass: 'fa fa-user',
    entries: []
  };
  private activeLanguagesMenuItem;

  constructor(
    private translateService: TranslateService,
    private configService: CoreConfigService,
    private userService: UserService
    ) {
    }

    ngOnInit() {
      this.translateService.use(this.lang);
      this.languages = this.configService.languages;
      for (const lang of this.languages) {
        const data: any = {name: lang};
        if (lang === this.lang) {
          data.active = true;
          this.activeLanguagesMenuItem = data;
        }
        this.languagesMenu.entries[0].entries.splice(0, 0, data);
      }
      const currentUser = this.userService.getCurrentUser();
      this.userMenu.entries.push({
        name: `${currentUser.first_name[0]}${currentUser.last_name[0]}`,
        entries: [
          {
            name: _('Logout'),
            href: `/logout`,
            iconCssClass: 'fa fa-sign-out'
          }
        ]

      });
      // const roles = this.userService.getCurrentUser().roles;

    }

    changeLang(item) {
      this.translateService.use(item.name);
      delete(this.activeLanguagesMenuItem.active);
      item.active = true;
      this.activeLanguagesMenuItem = item;
    }

}
