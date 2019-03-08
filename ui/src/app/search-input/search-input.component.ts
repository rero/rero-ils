import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-search-input',
  templateUrl: './search-input.component.html',
  styleUrls: ['./search-input.component.scss']
})
export class SearchInputComponent {

  @Input() placeholder = 'search';
  @Output() search = new EventEmitter<string>();
  @Input() searchText = '';

  doSearch(searchText: string) {
    this.search.emit(searchText);
  }
}
