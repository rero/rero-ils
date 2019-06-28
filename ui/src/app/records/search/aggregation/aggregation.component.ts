import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-aggregation',
  templateUrl: './aggregation.component.html',
  styleUrls: ['./aggregation.component.scss']
})
export class AggregationComponent {

  @Input() aggFilters = null;
  @Input() aggsSettings = null;
  @Input() aggregation = null;

  @Output() addAggFilter = new EventEmitter<{term: string, value: string}>();
  @Output() removeAggFilter = new EventEmitter<{term: string, value: string}>();

  private moreMode = true;

  isFiltered(term: any, value?: any) {
    if (value) {
      const filterValue = `${term}=${value}`;
      return this.aggFilters.some((val: any) => filterValue === val);
    } else {
      return this.aggFilters.some((val: any) => term === val.split('=')[0]);
    }
  }

  aggFilter(term: string, value: string) {
    if (this.isFiltered(term, value)) {
      this.removeAggFilter.emit({term: term, value: value});
    } else {
      this.addAggFilter.emit({term: term, value: value});
    }
  }

  isOpen(title: string) {
    if (this.isFiltered(title)) {
      return true;
    }
    if (this.aggsSettings.expand.some((value: any) => value === title)) {
      return true;
    }
    return false;
  }

  sizeOfBucket() {
    if (this.moreMode) {
      return this.aggsSettings.initialBucketSize;
    } else {
      return this.aggregation.buckets.length;
    }
  }

  displayMoreAndLessLink() {
    return this.aggregation.buckets.length > this.aggsSettings.initialBucketSize;
  }

  setMoreMode(state: boolean) {
    this.moreMode = state;
  }
}
