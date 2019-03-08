import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { RecordsService } from '../records.service';
import { RemoteSelectComponent } from './remote-select/remote-select.component';
import { RemoteInputComponent } from './remote-input/remote-input.component';
import { WidgetLibraryService } from 'angular6-json-schema-form';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService, AlertsService } from '@app/core';
import { TranslateService } from '@ngx-translate/core';

export function _(str: string) {
  return str;
}

@Component({
  selector: 'app-editor',
  templateUrl: './editor.component.html',
  styleUrls: ['./editor.component.scss']
})
export class EditorComponent implements OnInit {

  public schemaForm = null;
  public recordType = undefined;
  public pid = undefined;
  public message = undefined;
  public data;
  public redirectRecordType = undefined;
  public currentLocale = undefined;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private recordsService: RecordsService,
    private widgetLibrary: WidgetLibraryService,
    private alertsService: AlertsService,
    private apiService: ApiService,
    private translateService: TranslateService
  ) {
    this.widgetLibrary.registerWidget('select', RemoteSelectComponent);
    this.widgetLibrary.registerWidget('text', RemoteInputComponent);
    this.currentLocale = translateService.currentLang;
  }

  importFromEan(ean) {
    // 9782070541270
    this.recordsService.getRecordFromBNF(ean).subscribe(
      record => {
        if (record) {
          record.metadata['$schema'] = this.schemaForm.schema.properties['$schema'].default;
          this.schemaForm['data'] = record.metadata;
        } else {
          this.alertsService.addAlert('warning', _('EAN not found!'));
        }
      }
      );
  }

  ngOnInit() {
    combineLatest(this.route.params, this.route.queryParams)
    .pipe(map(results => ({params: results[0], query: results[1]})))
    .subscribe(results => {
      const params = results.params;
      const query = results.query;

      this.recordType = params.recordType;
      this.redirectRecordType = this.recordType;

      this.pid = params.pid;
      if (!this.pid) {
        let rec_type = this.recordType.replace(/ies$/, 'y');
        rec_type = rec_type.replace(/s$/, '');
        this.recordsService
        .getSchemaForm(this.recordType)
        .subscribe(schemaForm => {
          this.schemaForm = schemaForm;
          if (this.recordType === 'items' && query.document) {
            this.redirectRecordType = 'documents';
            const urlPerfix = this.apiService.getApiEntryPointByType('documents', true);
            this.schemaForm.schema.properties.document
              .properties['$ref']['default'] = urlPerfix + query.document;
          }
          if (this.recordType === 'locations' && query.library) {
            const urlPerfix = this.apiService.getApiEntryPointByType('libraries', true);
            this.redirectRecordType = 'libraries';
            this.schemaForm.schema.properties.library.properties['$ref']['default'] = urlPerfix + query.library;
          }
        });
      } else {
        this.recordsService.getRecord(params.recordType, this.pid).subscribe(record => {
          this.recordsService
          .getSchemaForm(this.recordType)
          .subscribe(schemaForm => {
            this.schemaForm = schemaForm;
            this.schemaForm['data'] = record.metadata;
            if (this.recordType === 'items') {
              this.redirectRecordType = 'documents';
            }
            if (this.recordType === 'locations') {
              this.redirectRecordType = 'libraries';
            }
          });
        });
      }
    });
  }

  save(record) {
    if (this.pid) {
      this.recordsService.update(this.recordType, record).subscribe(res => {
        this.alertsService.addAlert('info', _('Record Updated!'));
        this.router.navigate(['/records', this.redirectRecordType]);
      });
    } else {
      this.recordsService.create(this.recordType, record).subscribe(res => {
        this.alertsService.addAlert('info', _('Record Created with pid: ') + res['metadata']['pid']);
        this.router.navigate(['/records', this.redirectRecordType]);
      });
    }
  }

  cancel() {
    this.router.navigate(['/records', this.redirectRecordType]);
  }
}
