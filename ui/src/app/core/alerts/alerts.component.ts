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
