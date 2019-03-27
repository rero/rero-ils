import { Component, Input, OnInit } from '@angular/core';
import { TypeaheadMatch } from 'ngx-bootstrap';
import { Observable, of, combineLatest } from 'rxjs';
import { mergeMap, map } from 'rxjs/operators';
import { RecordsService } from '../records/records.service';
import { _ } from '@app/core';
import { TranslateStringService } from '../translate-string.service';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-autocomplete',
  templateUrl: './autocomplete.component.html',
  styleUrls: ['./autocomplete.component.scss']
})
export class AutocompleteComponent implements OnInit {

  asyncSelected = {
    text: undefined,
    query: undefined,
    index: undefined,
    pid: undefined,
    category: undefined
  };
  typeaheadLoading: boolean;
  typeaheadNoResults: boolean;
  dataSource: Observable<any>;
  @Input() action: string;
  @Input() size: string;
  @Input() placeholder: string;
  @Input()
  maxLengthSuggestion = 100;

  constructor(
    private recordsService: RecordsService,
    private route: ActivatedRoute,
    private translateStringService: TranslateStringService) {
    this.dataSource = Observable.create((observer: any) => {
      // Runs on every search
      observer.next(this.asyncSelected);
    })
    .pipe(
      mergeMap((token: any) => this.getStatesAsObservable(token.query))
      );
  }

  ngOnInit() {
    this.route.queryParamMap.subscribe((params: any) => {
      const query = params.get('q');
      if (query) {
        this.asyncSelected = {
          query: query,
          text: query,
          index: 'documents',
          pid: undefined,
          category: 'documents'
        };
      }
    });
  }

  getStatesAsObservable(token: string): Observable<any> {
    return combineLatest(
      this.recordsService.getSuggests('documents', 'autocomplete_title', token),
      this.recordsService.getSuggests('persons', 'autocomplete_name', token)
      )
    .pipe(
      map(
        ([documents, persons]) => {
          // add query at the top
          const values = [{
            text: token,
            query: token,
            pid: undefined,
            index: undefined,
            category: this.translateStringService.trans(_('your query')),
          }];
          // documents
          documents.hits.hits.map(hit => {
            let text = hit.metadata.title;
            let truncate = false;
            if (text.length > this.maxLengthSuggestion) {
              truncate = true;
              text = hit.metadata.title.substr(0, this.maxLengthSuggestion);
            }
            text = text.replace(new RegExp(token, 'gi'), `<b>${token}</b>`);
            if (truncate) {
              text = text + ' ...';
            }
            values.push({
              text: text,
              query: hit.metadata.title.replace(/[:\-\[\]()/"]/g, ' ').replace(/\s\s+/g, ' '),
              index: 'documents',
              pid: undefined,
              category: this.translateStringService.trans(_('documents'))
            });
          });
          // persons
          persons.hits.hits.map(hit => {
            let text = this.getPersonName(hit.metadata);
            text = text.replace(new RegExp(token, 'gi'), `<b>${token}</b>`);
            values.push({
              text: text,
              query: '',
              pid: hit.metadata.pid,
              index: 'persons',
              category: this.translateStringService.trans(_('direct links'))
            });
          });
          return values;
        })
      );
  }

  getPersonName(metadata) {
    for (const source of ['rero', 'bnf', 'gnd']) {
      if (metadata[source] && metadata[source].preferred_name_for_person) {
        return metadata[source].preferred_name_for_person;
      }
    }
  }

  changeTypeaheadLoading(e: boolean): void {
    this.typeaheadLoading = e;
  }

  typeaheadOnSelect(e: TypeaheadMatch): void {
    if (e.item.pid && e.item.index) {
      window.location.href = `/${e.item.index}/${e.item.pid}`;
    }
  }
}
