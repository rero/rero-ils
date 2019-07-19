import { Component, Input, OnInit } from '@angular/core';
import { BriefView } from './brief-view';
import { RecordsService } from '../../records.service';
import { TranslateService } from '@ngx-translate/core';

import { _, OrganisationViewService, } from '@app/core';


@Component({
  selector: 'app-documents-brief-view',
  template: `
  <article class="card flex-row border-0">
    <div class="align-self-start d-flex justify-content-center">
      <figure class="mb-0 thumb-brief">
        <img class="img-responsive border border-light " [src]="coverUrl">
        <figcaption class="text-center">{{ record.metadata.type | translate }}</figcaption>
      </figure>
    </div>
    <div class="card-body w-100 py-0">
      <h4 class="card-title mb-1">
        <a target="_self" href="/{{ viewCode }}/documents/{{ record.metadata.pid }}">{{ record.metadata.title }}</a>
      </h4>
      <article class="card-text">
        <!-- author -->
        <ul class="list-inline mb-0" *ngIf="record.metadata.authors && record.metadata.authors.length > 0">
          <li class="list-inline-item" *ngFor="let author of record.metadata.authors.slice(0,3); let last = last">
            <span *ngIf="!author.pid">
              {{ authorName(author) }}
              {{ author.qualifier ? author.qualifier : '' }}
              {{ author.date ? author.date : '' }}
            </span>
            <a *ngIf="author.pid" href="/{{ viewCode }}/persons/{{ author.pid }}">
              {{ authorName(author) }}
              {{ author.qualifier ? author.qualifier : '' }}
              {{ author.date ? author.date : '' }}
            </a>
            {{ last ? '' : '; ' }}

          </li>
          <li *ngIf="record.metadata.authors && record.metadata.authors.length > 3">; …</li>
        </ul>

        <!-- is_part_of -->
        <span *ngIf="record.metadata.is_part_of">{{ record.metadata.is_part_of }}</span>

        <!-- publishers -->
        <ul class="list-inline mb-0" *ngIf='record.metadata.publishers && record.metadata.publishers.length > 0'>
          <li class="list-inline-item" *ngFor='let publisher of record.metadata.publishers; let last = last'>
            <span *ngIf="publisher.place">{{ publisher.place.join(', ') }}</span><span *ngIf="publisher.place">: </span>
            <span *ngIf="publisher.name">{{ publisher.name.join(', ') }}</span>
            {{ last ? '' : '; ' }}
          </li>
        </ul>

        <!-- publicationDate -->
        <span *ngIf="record.metadata.publicationYear && !record.metadata.freeFormedPublicationDate">
          {{ record.metadata.publicationYear }}
        </span>
        <span *ngIf="record.metadata.freeFormedPublicationDate">{{ record.metadata.freeFormedPublicationDate }}</span>
        <div *ngIf="record.metadata.type !== 'ebook'">
          <i class="fa fa-circle text-{{ record.metadata.available ? 'success' : 'danger' }}" aria-hidden="true"></i>&nbsp;
          <span translate *ngIf="record.metadata.available">available</span>
          <span translate *ngIf="!record.metadata.available">not available</span>
        </div>
        <div *ngIf="record.explanation">
          <a class="badge badge-info collapsed"
              data-toggle="collapse" href="#{{'score'+record.metadata.pid }}"
              aria-expanded="false">
              score: {{ record.explanation.value }}
          </a>
          <pre class="collapse border border-secondary mt-1" id="{{'score'+record.metadata.pid }}">{{record.explanation|json}}</pre>
        </div>
      </article>
    </div>
</article>
`,
  styles: [`
.thumb-brief
  img {
    max-height: 90px;
    width: 58px;
  }

@media (max-width: 960px) {
  .thumb-brief
    img {
      max-width: 48px;
    }
  }

pre {
  white-space: pre-wrap;
  max-height: 300px;
  font-size: 0.7em;
}
`]
})
export class PublicDocumentsBriefViewComponent implements OnInit, BriefView {
  @Input()
  set record(value) {
    if (value !== undefined) {
      this._record = value;
      this.coverUrl = `/static/images/icon_${value.metadata.type}.png`;
      if (value.metadata.cover_art) {
        this.coverUrl = value.metadata.cover_art;
      } else if (value.metadata.identifiers) {
        const isbn = value.metadata.identifiers.isbn;
        if (isbn) {
          this.getCover(isbn);
        }
      }
    }
  }

  get record() {
    return this._record;
  }
  private _record: any;

  coverUrl: string;

  public viewCode = undefined;

  constructor(
    private recordsService: RecordsService,
    private translate: TranslateService,
    private organisationView: OrganisationViewService
  ) {}

  ngOnInit() {
    this.viewCode = this.organisationView.getViewCode();
  }

  authorName(author) {
    const name_index = `name_${this.translate.currentLang}`;
    let name_lng = author[name_index];
    if (!name_lng) {
      name_lng = author['name'];
    }
    return name_lng;
  }

  getCover(isbn) {
    this.recordsService.getCover(isbn).subscribe(result => {
      if (result.success) {
        this.coverUrl = result.image;
      }
    });
  }
}
