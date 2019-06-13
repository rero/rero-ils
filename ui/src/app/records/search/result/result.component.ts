import { Component, OnInit, Input, Output, EventEmitter, ViewChild, ComponentFactoryResolver } from '@angular/core';
import { BriefViewDirective } from '../brief-view/brief-view.directive';
import { BriefView } from '../brief-view/brief-view';
import { JsonBriefViewComponent } from '../brief-view/json-brief-view.component';
import { ItemTypesBriefViewComponent } from '../brief-view/item-types-brief-view.component';
import { PatronTypesBriefViewComponent } from '../brief-view/patron-types-brief-view.component';
import { CircPoliciesBriefViewComponent } from '../brief-view/circ-policies-brief-view.component';
import { PatronsBriefViewComponent } from '../brief-view/patrons-brief-view.component';
import { LibrariesBriefViewComponent } from '../brief-view/libraries-brief-view.component';
import { DocumentsBriefViewComponent } from '../brief-view/documents-brief-view.component';
import { PersonsBriefViewComponent } from '../brief-view/persons-brief-view.component';
import { PublicDocumentsBriefViewComponent } from '../brief-view/public-documents-brief-view.component';


@Component({
  selector: 'app-result',
  templateUrl: './result.component.html',
  styleUrls: ['./result.component.scss']
})
export class ResultComponent implements OnInit {

  @Input() record: any;
  @Input() adminMode: boolean;
  @Input() briefViewName: any;
  @Output() deletedRecord = new EventEmitter<string>();

  @ViewChild(BriefViewDirective) briefView: BriefViewDirective;
  briefViews = {
      item_types: ItemTypesBriefViewComponent,
      patron_types: PatronTypesBriefViewComponent,
      circ_policies: CircPoliciesBriefViewComponent,
      patrons: PatronsBriefViewComponent,
      persons: PersonsBriefViewComponent,
      libraries: LibrariesBriefViewComponent,
      documents: DocumentsBriefViewComponent,
      public_documents: PublicDocumentsBriefViewComponent,
      public_persons: PersonsBriefViewComponent,
  };
  defaultBriefView = JsonBriefViewComponent;

  constructor(
    private componentFactoryResolver: ComponentFactoryResolver
  ) { }

  ngOnInit() {
    this.loadBriefView();
  }

  loadBriefView() {
    let component = this.defaultBriefView;
    if (this.briefViews[this.briefViewName]) {
      component = this.briefViews[this.briefViewName];
    }
    const componentFactory = this.componentFactoryResolver.resolveComponentFactory(component);
    const viewContainerRef = this.briefView.viewContainerRef;
    viewContainerRef.clear();

    const componentRef = viewContainerRef.createComponent(componentFactory);
    (<BriefView>componentRef.instance).record = this.record;
  }

  hasPermissionToDelete() {
    const record = this.record;
    if (record.permissions
      && record.permissions.cannot_delete
      && record.permissions.cannot_delete.permission) {
      return false;
    }
    return true;
  }

  hasPermissionToUpdate() {
    const record = this.record;
    if (record.permissions
        && record.permissions.cannot_update
        && record.permissions.cannot_update.permission) {
      return false;
    }
    return true;
  }

  deleteRecord(pid: string) {
    this.deletedRecord.emit(pid);
  }
}
