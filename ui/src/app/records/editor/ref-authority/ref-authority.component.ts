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

import { AbstractControl } from '@angular/forms';
import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { JsonSchemaFormService } from 'angular6-json-schema-form';
import { Observable, of } from 'rxjs';
import { debounceTime, mergeMap, map } from 'rxjs/operators';
import { RecordsService } from '../../records.service';
import { TypeaheadMatch } from 'ngx-bootstrap';
import { UserService } from '../../../user.service';
import { _ } from '@app/core';
import { TranslateService} from '@ngx-translate/core';
import * as moment from 'moment';

@Component({
  // tslint:disable-next-line:component-selector
  selector: 'app-ref-authority',
  templateUrl: './ref-authority.component.html',
  styleUrls: ['./ref-authority.component.scss']
})
export class RefAuthorityComponent implements OnInit, OnDestroy {
  formControl: AbstractControl;
  controlName: string;
  controlValue: string;
  controlDisabled = false;
  boundControl = false;
  options: any;
  autoCompleteList: string[] = [];
  @Input() layoutNode: any;
  @Input() layoutIndex: number[];
  @Input() dataIndex: number[];

  asyncSelected = {
    name: undefined,
    ref: undefined,
    query: undefined,
    category: undefined
  };
  dataSource: Observable<any>;
  typeaheadLoading: boolean;
  private currentLocale = undefined;
  private userSettings = undefined;

  constructor(
    private jsf: JsonSchemaFormService,
    private recordsService: RecordsService,
    private userService: UserService,
    private translateService: TranslateService
    ) {
  }

  extractDate(date) {
    const mDate = moment(date, ['YYYY', 'YYYY-MM', 'YYYY-MM-DD']);
    if (mDate.isValid()) {
      return mDate.format('YYYY');
    }
    return date;
  }

  ngOnInit() {
    this.options = this.layoutNode.options || {};
    this.userService.userSettings.subscribe(userSettings => this.userSettings = userSettings);
    this.jsf.initializeControl(this);
    if (this.controlValue) {
      const pid = this.controlValue.split('/').pop();
      this.recordsService.getRecord('mef', pid, 1).subscribe( authority => {
        this.asyncSelected = {
          name: this.getName(authority.metadata),
          ref: this.controlValue,
          query: undefined,
          category: this.translateService.instant(_('link to authority'))
        };
        this.jsf.updateValue(this, this.controlValue);
      });
    } else {
      const name = this.formControl.parent.get('name').value;
      this.asyncSelected = {
        name: name,
        ref: undefined,
        query: name,
        category: this.translateService.instant(_('create'))
      };
    }
    this.dataSource = Observable.create((observer: any) => {
      // Runs on every search
      observer.next(this.asyncSelected);
    })
    .pipe(
      mergeMap((token: any) => this.getAuthoritySuggestions(token.query))
      );
  }

  valueChanged(value) {
    const formControlParent = this.formControl.parent;
    formControlParent.get('name').setValue(value);
  }

  getAuthoritySuggestions(query) {
    if (!query) {
      return of([]);
    }
    const esQuery = `%5C*.preferred_name_for_person:'${query}'`;
    return this.recordsService.getRecords('global', 'mef', 1, 10, esQuery).pipe(
      map(results => {
        const names = [{
          name: query,
          ref: undefined,
          query: query,
          category: this.translateService.instant(_('create'))
        }];
        if (!results) {
          return [];
        }
        results.hits.hits.map(hit => {
          names.push({
            name: this.getName(hit.metadata),
            ref: `https://mef.rero.ch/api/mef/${hit.metadata.pid}`,
            query: query,
            category: this.translateService.instant(_('link to authority'))
          });
        });
        return names;
      })
      );
  }

  getName(metadata) {
    if (this.userSettings) {
      for (const source of this.userSettings.personsLabelOrder) {
        if (metadata[source]) {
          const data = metadata[source];
          let name = data.preferred_name_for_person;
          if (data.date_of_birth || data.date_of_death) {
            name += ', ';
            if (data.date_of_birth) {
              name += this.extractDate(data.date_of_birth);
            }
            name += ' - ';
            if (data.date_of_death) {
              name += this.extractDate(data.date_of_death);
            }
          }
          return name;
        }
      }
    }
    // TODO: add exception or error
  }

  updateValue(event) {
    this.jsf.updateValue(this, event.target.value);
  }

  changeTypeaheadLoading(e: boolean): void {
    this.typeaheadLoading = e;
  }

  typeaheadOnSelect(e: TypeaheadMatch): void {
    const formControlParent = this.formControl.parent;

    if (e.item.ref !== undefined) {
      this.jsf.updateValue(this, e.item.ref);
      formControlParent.get('name').setValue(undefined);
      formControlParent.get('date').setValue(undefined);
      formControlParent.get('qualifier').setValue(undefined);
    } else {
      formControlParent.get('name').setValue(e.item.name);
    }
    this.asyncSelected = e.item;
  }

  ngOnDestroy() {
    const formControlParent = this.formControl.parent;

    // TODO: check to be sure that the value is submitted before this
    this.formControl.setValue(undefined);
    formControlParent.get('name').setValue(undefined);
    formControlParent.get('date').setValue(undefined);
    formControlParent.get('qualifier').setValue(undefined);
  }
}
