import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { RecordsService } from '../../records.service';
import { OrganisationViewService } from '@app/core';
import { combineLatest } from 'rxjs';
import { map } from 'rxjs/operators';

@Component({
  selector: 'app-public-search',
  templateUrl: './public-search.component.html',
  styleUrls: ['./public-search.component.scss']
})
export class PublicSearchComponent implements OnInit {

  viewCode = undefined;
  query = '';
  nDocuments = undefined;
  nPersons = undefined;

  constructor(
    private route: ActivatedRoute,
    private recordsService: RecordsService,
    private organisationView: OrganisationViewService
  ) { }

  ngOnInit() {
    combineLatest(
      this.route.params,
      this.route.queryParamMap
    ).pipe(map(results => ({
      params: results[0],
      query: results[1]
    })))
    .subscribe(results => {
      this.viewCode = results.params.viewcode;
      this.organisationView.setViewCode(results.params.viewcode);
      const query = results.query.get('q');
      if (query) {
        this.query = query;
      }
      this.getCount();
    });
  }

  getCount() {
    this.recordsService.getRecords(this.viewCode, 'documents', 1, 0, this.query).subscribe(results => {
      this.nDocuments = results.hits.total;
    });
    this.recordsService.getRecords(this.viewCode, 'persons', 1, 0, this.query).subscribe(results => {
      this.nPersons = results.hits.total;
    });
  }
}
