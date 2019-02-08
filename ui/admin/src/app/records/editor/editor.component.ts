import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { RecordsService } from '../records.service';
import { RemoteSelectComponent } from './remote-select/remote-select.component';
import { RemoteInputComponent } from './remote-input/remote-input.component';
import { WidgetLibraryService } from 'angular6-json-schema-form';
import { OpeningHoursComponent } from './opening-hours/opening-hours.component';
import { ExceptionDatesComponent } from './exception-dates/exception-dates.component';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

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

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private recordsService: RecordsService,
    private widgetLibrary: WidgetLibraryService
  ) {
    this.widgetLibrary.registerWidget('select', RemoteSelectComponent);
    this.widgetLibrary.registerWidget('text', RemoteInputComponent);
    this.widgetLibrary.registerWidget('opening-hours', OpeningHoursComponent);
    this.widgetLibrary.registerWidget('exception-dates', ExceptionDatesComponent);
  }

  importFromEan(ean) {
    // 9782070541270
    this.recordsService.getRecordFromBNF(ean).subscribe(
      record => {
        if (record) {
          record.metadata['$schema'] = this.schemaForm.schema.properties['$schema'].default;
          this.schemaForm['data'] = record.metadata;
          console.log(this.schemaForm);
        } else {
          this.message = 'EAN not found!';
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
            this.schemaForm.schema.properties.document.properties['$ref']['default'] = 'http://ils.rero.ch/api/documents/' + query.document;
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
          });
        });
      }
    });
  }

  save(record) {
    if (this.pid) {
      this.recordsService.update(this.recordType, record).subscribe(res => {
        this.message = 'Record Updated';
        this.router.navigate(['/records', this.redirectRecordType]);
      });
    } else {
      this.recordsService.create(this.recordType, record).subscribe(res => {
        this.message = `Record Created with pid: ${record['metadata']['pid']}`;
        this.router.navigate(['/records', this.redirectRecordType]);
      });
    }
  }

  cancel() {
    this.router.navigate(['/records', this.redirectRecordType]);
  }
}
