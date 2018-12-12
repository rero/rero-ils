import { Component, OnInit, Input, ViewChild, ChangeDetectorRef } from '@angular/core';
import { Subject } from 'rxjs';
import { DataTableDirective } from 'angular-datatables';

@Component({
  selector: 'app-requested-items-list',
  templateUrl: './requested-items-list.component.html',
  styleUrls: ['./requested-items-list.component.scss']
})
export class RequestedItemsListComponent implements OnInit {

  @ViewChild(DataTableDirective)
  dtOptions: DataTables.Settings = {};
  dtTrigger: Subject<any> = new Subject();
  private _items = null;

  @Input() set items(values) {
    if (values) {
      this._items = values;
      this.ref.markForCheck();
      this.dtTrigger.next();
    }
  }

  constructor(private ref: ChangeDetectorRef) {}

  get items() {
    return this._items;
  }

  ngOnInit(): void {
    this.dtOptions = {
      searching: false,
      info: false,
      paging: false,
      destroy: true,
      retrieve: true
    };
  }

}
