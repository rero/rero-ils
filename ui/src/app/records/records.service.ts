import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { catchError, map, debounceTime } from 'rxjs/operators';
import { of, Subject } from 'rxjs';

import { TranslateService } from '@ngx-translate/core';
import { I18nPluralPipe, NgLocaleLocalization } from '@angular/common';
import { DialogService, _ } from '@app/core';

@Injectable({
  providedIn: 'root'
})
export class RecordsService {
  private translatePlural;
  constructor(
    private http: HttpClient,
    private dialogService: DialogService,
    private translateService: TranslateService

  ) {
    this.translatePlural = new I18nPluralPipe(
      new NgLocaleLocalization(this.translateService.currentLang));
  }

  getCover(isbn: string) {
    const url = `/api/cover/${isbn}`;
    return this.http.get<any>(url).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
    );
  }

  getRecords(
    record_type: string,
    page: number = 1,
    size: number = 10,
    query: string = '',
    mime_type: string = 'application/json',
    filters = [],
    sort?,
    displayScore?
  ) {
    let url = `/api/${record_type}/?page=${page}&size=${size}&q=${query}`;
    if (filters.length) {
      url = url + '&' + filters.join('&');
    }
    if (sort) {
      url = url + `&sort=${sort}`;
    }
    if (displayScore) {
      url = url + `&display_score=${displayScore}`;
    }
    return this.http.get<any>(url, this.httpOptions(mime_type)).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
    );
  }

  getSuggests(
    record_type: string,
    field: string,
    query: string,
    mime_type: string = 'application/json'
  ) {
    const url = `/api/${record_type}/?q=${field}:${query}&size=5`;
    return this.http.get<any>(url, this.httpOptions(mime_type)).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
    );
  }

  getRecord(
    record_type: string,
    pid: string,
    resolve = 0,
    mime_type: string = 'application/json'
  ) {
    const url = `/api/${record_type}/${pid}?resolve=${resolve}`;
    return this.http.get<any>(url, this.httpOptions(mime_type)).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
    );
  }

  getRecordFromBNF(ean) {
    const url = `/api/import/bnf/${ean}`;
    return this.http.get<any>(url).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
    );
  }

  delete(record_type: string, pid: string) {
    const url = `/api/${record_type}/${pid}`;
    return this.http.delete<any>(url).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
    );
  }

  getSchema(record_type) {
    let rec_type = record_type.replace(/ies$/, 'y');
    rec_type = rec_type.replace(/s$/, '');
    const url = `/schema/${record_type}/${rec_type}-v0.0.1.json`;
    return this.http.get<any>(url).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      }),
      map(data => {
        delete data['$schema'];
        return data;
      })
    );
  }

  getSchemaForm(record_type) {
    return this.http.get<any>(`/schemaform/${record_type}`);
  }

  create(record_type, record) {
    const url = `/api/${record_type}/`;
    return this.http.post(url, record);
  }

  update(record_type, record) {
    const url = `/api/${record_type}/${record.pid}`;
    return this.http.put(url, record);
  }

  valueAlreadyExists(record_type, field, value, excludePid) {
    let url = `/api/${record_type}/?size=0&q=${field}:"${value}"`;
    if (excludePid) {
      url += ` NOT pid:${excludePid}`;
    }
    return this.http.get<any>(url).pipe(
      map(res => res.hits.total),
      map(total => total ? { alreadyTakenMessage: value } : null),
      debounceTime(1000)
    );
  }


  deleteRecord(pid, recordType) {
    const success = new Subject();
    this.getRecord(
      recordType,
      pid,
      0,
      'application/json'
    ).subscribe(record => {
      const data = record.permissions;
      const canDeleted = !('cannot_delete' in data);
      const config = {
        ignoreBackdropClick: true,
        initialState: {
          title: this.translateService.instant(_('Confirmation')),
          body: canDeleted ?
            this.translateService.instant(
              _('Do you really want to delete this record ?')
            ) :
            this.dialogMessage(data['cannot_delete']),
          confirmButton: canDeleted,
          confirmTitleButton: _('Delete'),
          cancelTitleButton: canDeleted ? _('Cancel') : _('OK')
        }
      };
      this.dialogService.show(config).subscribe((confirm: boolean) => {
        if (confirm) {
          this.delete(recordType, pid)
          .subscribe(() => {
            success.next(true);
          });
        } else {
          success.next(false);
        }
      });
    });
    return success;
  }

  private dialogMessage(data: any) {
    const messages = [];
    let plurialdict = {};
    if ('links' in data) {
      plurialdict = this.plurialLinksMessages();
      Object.keys(data['links']).forEach(element => {
        let message = null;
        if ((element in plurialdict)) {
          message = this.translatePlural.transform(
            data['links'][element],
            plurialdict[element],
            this.translateService.currentLang
          );
        } else {
          message = data['links'][element] + ' ' + element;
        }
        messages.push('- ' + message);
      });
    }
    if ('others' in data) {
      plurialdict = this.othersMessages();
      Object.keys(data['others']).forEach(element => {
        if ((element in plurialdict)) {
          messages.push('- ' + plurialdict[element]);
        } else {
          messages.push('- ' + element);
        }
      });
    }
    messages.unshift(
      this.translateService.instant(messages.length === 1 ?
      _('You cannot delete the record for the following reason:') :
      _('You cannot delete the record for the following reasons:')
    ));
    return messages.join('\n');
  }

  private plurialLinksMessages() {
    return {
      'circ_policies': {
        '=1': this.translateService.instant(_('has 1 circulation policy attached')),
        'other': this.translateService.instant(_('has # circulation policies attached'))
      },
      'documents': {
        '=1': this.translateService.instant(_('has 1 document attached')),
        'other': this.translateService.instant(_('has # documents attached'))
      },
      'item_types': {
        '=1': this.translateService.instant(_('has 1 item type attached')),
        'other': this.translateService.instant(_('has # item types attached'))
      },
      'items': {
        '=1': this.translateService.instant(_('has 1 item attached')),
        'other': this.translateService.instant(_('has # items attached'))
      },
      'libraries': {
        '=1': this.translateService.instant(_('has 1 library attached')),
        'other': this.translateService.instant(_('has # libraries attached'))
      },
      'loans': {
        '=1': this.translateService.instant(_('has 1 loan attached')),
        'other': this.translateService.instant(_('has # loans attached'))
      },
      'locations': {
        '=1': this.translateService.instant(_('has 1 location attached')),
        'other': this.translateService.instant(_('has # locations attached'))
      },
      'organisations': {
        '=1': this.translateService.instant(_('has 1 organisation attached')),
        'other': this.translateService.instant(_('has # organisations attached'))
      },
      'patron_types': {
        '=1': this.translateService.instant(_('has 1 patron type attached')),
        'other': this.translateService.instant(_('has # patron types attached'))
      },
      'patrons': {
        '=1': this.translateService.instant(_('has 1 patron attached')),
        'other': this.translateService.instant(_('has # patrons attached'))
      }
    };
  }

  private othersMessages() {
    return {
      'is_default': this.translateService.instant(_('The default record cannot be deleted')),
      'has_settings': this.translateService.instant(_('The record contains settings')),
      'harvested': this.translateService.instant(_('The record has been harvested'))
    };
  }

  private httpOptions(mime_type: string) {
    return {
      headers: new HttpHeaders({
        'Accept': mime_type
      })
    };
  }
}
