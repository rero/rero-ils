import { Component, Input } from '@angular/core';
import { TypeaheadMatch } from 'ngx-bootstrap';
import { Observable, of } from 'rxjs';
import { mergeMap, map } from 'rxjs/operators';
import { RecordsService } from '../records/records.service';
import { _ } from '@app/core';
import { TranslateStringService } from '../translate-string.service';

@Component({
  selector: 'app-autocomplete',
  templateUrl: './autocomplete.component.html',
  styleUrls: ['./autocomplete.component.scss']
})
export class AutocompleteComponent {

  asyncSelected = {
    text: undefined,
    query: undefined,
    index: undefined
  };
  typeaheadLoading: boolean;
  typeaheadNoResults: boolean;
  dataSource: Observable<any>;
  @Input() action: string;
  @Input() size: string;
  @Input() placeholder: string;

  constructor(
    private recordsService: RecordsService,
    private translateStringService: TranslateStringService) {
    this.dataSource = Observable.create((observer: any) => {
      // Runs on every search
      observer.next(this.asyncSelected);
    })
      .pipe(
        mergeMap((token: any) => this.getStatesAsObservable(token.query))
      );
  }

  getStatesAsObservable(token: string): Observable<any> {
    return this.recordsService.getSuggests('documents', 'autocomplete_title', token).pipe(
      map(suggests => {
        const values = [{
          text: token,
          query: token,
          index: this.translateStringService.trans(_('your query'))
        }];
        suggests.hits.hits.map(hit => {
          values.push({
            text: hit.metadata.title.substr(0, 100).replace(new RegExp(token, 'gi'), `<b>${token}</b>`) + '...',
            query: hit.metadata.title,
            index: 'documents'
          });
        });
        return values;
      })
    );
  }

  changeTypeaheadLoading(e: boolean): void {
    this.typeaheadLoading = e;
  }

  // typeaheadOnSelect(e: TypeaheadMatch): void {
  //   console.log("Selected item: ", e.item);
  // }
}
