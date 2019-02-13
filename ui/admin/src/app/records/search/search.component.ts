import { Component, OnInit, LOCALE_ID, Inject } from '@angular/core';
import { RecordsService } from '../records.service';
import { ActivatedRoute } from '@angular/router';
import { AlertsService, DialogService } from '@app/core';
import { TranslateService } from '@ngx-translate/core';
import { I18nPluralPipe } from '@angular/common';

export function _(str: string) {
  return str;
}

@Component({
  selector: 'app-search',
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.scss']
})
export class SearchComponent implements OnInit {

  public records: Object[] = [];
  public total = 0;
  public nPerPage = 10;
  public currentPage = 1;
  public recordType = undefined;
  public query = '';
  public placeholder = '';
  public notFound = false;
  private locale: string;

  constructor(
    private recordsService: RecordsService,
    private route: ActivatedRoute,
    private alertsService: AlertsService,
    private dialogService: DialogService,
    private translateService: TranslateService,
    private translatePlurial: I18nPluralPipe,
    @Inject(LOCALE_ID) locale: string
  ) {
    this.locale = locale;
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
      this.recordType = params.recordType;
      this.placeholder = `search in ${this.recordType}`;
      this.getRecords();
    });
  }

  getRecords() {
    this.recordsService.getRecords(
      this.recordType,
      this.currentPage,
      this.nPerPage,
      this.query
    ).subscribe(data => {
      if (data === null) {
        this.notFound = true;
        this.alertsService.addAlert('info', _('No result found.'));
      } else {
        this.records = data.hits.hits;
        this.total = data.hits.total;
        if (this.records.length === 0 && this.currentPage > 1) {
          this.currentPage -= 1;
          this.getRecords();
        }
        if (data.hits.total === 0) {
          this.alertsService.addAlert('info', _('No result found.'));
        }
      }
    });
  }

  showPagination() {
    if (this.total > this.nPerPage) {
      return true;
    }
    return false;
  }

  pageChanged(event: any): void {
    this.currentPage = event.page;
    this.nPerPage = event.itemsPerPage;
    this.getRecords();
  }

  searchValueUpdated(searchValue: string) {
    this.query = searchValue;
    this.getRecords();
  }

  deleteRecord(pid) {
    this.recordsService.getRecord(
      this.recordType,
      pid,
      0,
      'application/can-delete+json'
    ).subscribe(record => {
      const data = record.metadata;
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
          this.recordsService
          .delete(this.recordType, pid)
          .subscribe(() => {
            this.alertsService.addAlert('warning', _('Record deleted.'));
            this.getRecords();
          });
        }
      });
    });
  }

  private dialogMessage(data: any) {
    const messages = [];
    let plurialdict = {};
    if ('links' in data) {
      plurialdict = this.plurialLinksMessages();
      Object.keys(data['links']).forEach(element => {
        let message = null;
        if ((element in plurialdict)) {
          message = this.translatePlurial.transform(
            data['links'][element],
            plurialdict[element],
            this.locale
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
          messages.push('- ' + this.translateService.instant(
            plurialdict[element]
          ));
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
      'is_default': _('The default record cannot be deleted'),
      'has_settings': _('The recording contains settings')
    };
  }
}
