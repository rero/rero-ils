import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { RecordsService } from '../../records.service';

@Component({
  selector: 'app-public-search',
  templateUrl: './public-search.component.html',
  styleUrls: ['./public-search.component.scss']
})
export class PublicSearchComponent implements OnInit {
  query = '';
  nDocuments = undefined;
  nPersons = undefined;
  constructor(
    private route: ActivatedRoute,
    private recordsService: RecordsService
  ) { }

  ngOnInit() {
    this.route.queryParamMap.subscribe((params: any) => {
      const query = params.get('q');
      if (query) {
        this.query = query;
      }
      this.getCount();
    });
  }

  getCount() {
    this.recordsService.getRecords('documents', 1, 0, this.query).subscribe(results => {
      this.nDocuments = results.hits.total;
    });
    this.recordsService.getRecords('persons', 1, 0, this.query).subscribe(results => {
      this.nPersons = results.hits.total;
    });
  }

}
