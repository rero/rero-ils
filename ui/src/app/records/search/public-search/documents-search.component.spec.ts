import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DocumentsSearchComponent } from './documents-search.component';

describe('DocumentsSearchComponent', () => {
  let component: DocumentsSearchComponent;
  let fixture: ComponentFixture<DocumentsSearchComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DocumentsSearchComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DocumentsSearchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
