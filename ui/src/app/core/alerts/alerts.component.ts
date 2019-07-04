/*

RERO ILS
Copyright (C) 2019 RERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

*/

import { Component, OnInit } from '@angular/core';
import { AlertComponent } from 'ngx-bootstrap/alert/alert.component';
import { AlertsService } from './alerts.service';

@Component({
  selector: 'app-alerts',
  templateUrl: './alerts.component.html',
  styleUrls: ['./alerts.component.scss']
})
export class AlertsComponent implements OnInit {

  private alertTimeout = 5000;
  public alerts: any[] = [];

  constructor(
    private alertsService: AlertsService
  ) { }

  ngOnInit() {
    this.alertsService.alert.subscribe(alert => {
      if (alert) {
        this.addAlert(alert.type, alert.message);
      }
    });
  }

  onAlertClosed(dismissedAlert: AlertComponent): void {
    this.alerts = this.alerts.filter(alert => alert !== dismissedAlert);
  }

  addAlert(type, message) {
    this.alerts.push({
      type: type,
      message: message,
      timeout: this.alertTimeout
    });
  }
}
