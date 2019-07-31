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

import { Component, OnInit, Inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { RecordsService } from '../records.service';
import { RemoteSelectComponent } from './remote-select/remote-select.component';
import { RemoteInputComponent } from './remote-input/remote-input.component';
import { RefAuthorityComponent } from './ref-authority/ref-authority.component';
import { RolesCheckboxesComponent } from './roles-checkboxes/roles-checkboxes.component';
import { JsonPointer } from 'angular6-json-schema-form';
import { WidgetLibraryService } from 'angular6-json-schema-form';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService } from '@app/core';
import { TranslateService } from '@ngx-translate/core';
import { Location } from '@angular/common';
import { ToastrService } from 'ngx-toastr';
import { FieldsetComponent } from './fieldset/fieldset.component';
import { FrameworkLibraryService } from 'angular6-json-schema-form';
import { CustomBootstrap4Framework } from './bootstrap4-framework/custombootstrap4-framework';
import { AddReferenceComponent } from './add-reference/add-reference.component';
import { UserService } from '../../user.service';
// import { Bootstrap4Framework } from 'angular6-json-schema-form';
// import { Framework } from 'angular6-json-schema-form';

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
  public currentLocale = undefined;
  public formValidationErrors: any;
  private userSettings = undefined;
  private goToDetailedView = false;
  constructor(
    @Inject(CustomBootstrap4Framework) bootstrap4framework,
    private route: ActivatedRoute,
    private router: Router,
    private recordsService: RecordsService,
    private widgetLibrary: WidgetLibraryService,
    private apiService: ApiService,
    private translateService: TranslateService,
    private location: Location,
    private toastrService: ToastrService,
    private frameworkLibrary: FrameworkLibraryService,
    private userService: UserService
  ) {
    // TODO: remove this bad hack when the following PR will be integrated
    // https://github.com/hamzahamidi/Angular6-json-schema-form/pull/64
    this.frameworkLibrary.frameworkLibrary['rero'] = bootstrap4framework;

    this.widgetLibrary.registerWidget('select', RemoteSelectComponent);
    this.widgetLibrary.registerWidget('rolesCheckboxes', RolesCheckboxesComponent);
    this.widgetLibrary.registerWidget('text', RemoteInputComponent);
    this.widgetLibrary.registerWidget('refAuthority', RefAuthorityComponent);
    this.widgetLibrary.registerWidget('fieldset', FieldsetComponent);
    this.widgetLibrary.registerWidget('$ref', AddReferenceComponent);

    this.currentLocale = translateService.currentLang;
    this.userService.userSettings.subscribe(settings => this.userSettings = settings);
  }

  importFromEan(ean) {
    // 9782070541270
    this.recordsService.getRecordFromBNF(ean).subscribe(
      record => {
        if (record) {
          record.metadata['$schema'] = this.schemaForm.schema.properties['$schema'].default;
          this.schemaForm['data'] = record.metadata;
        } else {
          this.toastrService.warning(
            _('EAN not found!'),
            _('Import')
          );
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

      this.pid = params.pid;
      try {
        this.goToDetailedView = Boolean(JSON.parse(query.go_to_detailed));
      } catch (e) {
        console.log(`unable to parse query option: ${query.go_to_detailed}`);
      }
      if (!this.pid) {
        let rec_type = this.recordType.replace(/ies$/, 'y');
        rec_type = rec_type.replace(/s$/, '');
        this.recordsService
        .getSchemaForm(this.recordType)
        .subscribe(schemaForm => {
          this.schemaForm = schemaForm;
          if (this.recordType === 'items' && query.document) {
            const urlPerfix = this.apiService.getApiEntryPointByType('documents', true);
            this.schemaForm.schema.properties.document
              .properties['$ref']['default'] = urlPerfix + query.document;
          }
          if (this.recordType === 'locations' && query.library) {
            const urlPerfix = this.apiService.getApiEntryPointByType('libraries', true);
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
          });
        });
      }
    });
  }

  save(record) {
    if (this.pid) {
      this.recordsService.update(this.recordType, record).subscribe(res => {
        this.toastrService.success(
          _('Record Updated!'),
          _(this.recordType)
        );
        console.log(res);
        this.goToNext(this.pid);
      });
    } else {
      this.recordsService.create(this.recordType, record).subscribe(res => {
        this.toastrService.success(
          _('Record Created with pid: ') + res['metadata']['pid'],
          _(this.recordType)
        );
        this.goToNext(res['metadata']['pid']);
      });
    }
  }

  goToNext(pid) {
    console.log(this.goToDetailedView, this.userSettings, document.referrer, window.location);
    if (this.goToDetailedView && this.userSettings !== undefined) {
      window.location.href = `/${this.userSettings.global_view}/${this.recordType}/${pid}`;
    } else {
      if (document.referrer.search(/admin/)) {
        this.location.back();
      } else {
        window.location.href = document.referrer + '?nocache=' + (new Date()).getTime();
      }
    }
  }

  cancel() {
    this.location.back();
  }

  get prettyValidationErrors() {
    if (!this.formValidationErrors) { return null; }
    const errorArray = [];
    for (const error of this.formValidationErrors) {
      const message = error.message;
      const dataPathArray = JsonPointer.parse(error.dataPath);
      if (dataPathArray.length) {
        let field = dataPathArray[0];
        for (let i = 1; i < dataPathArray.length; i++) {
          const key = dataPathArray[i];
          field += /^\d+$/.test(key) ? `[${key}]` : `.${key}`;
        }
        errorArray.push(`${field}: ${message}`);
      } else {
        errorArray.push(message);
      }
    }
    return errorArray.join('<br>');
  }

  validationErrors(errors) {
    this.formValidationErrors = errors;
  }
}
