import { Component, OnInit, Input, OnChanges, AfterViewInit, ViewChild, SimpleChanges, OnDestroy } from '@angular/core';
import { Loan } from '../loans';
import { Subject } from 'rxjs';
import { DataTableDirective } from 'angular-datatables';

@Component({
  selector: 'app-requested-loans-list',
  templateUrl: './requested-loans-list.component.html',
  styleUrls: ['./requested-loans-list.component.scss']
})
export class RequestedLoansListComponent implements OnInit, OnChanges, AfterViewInit, OnDestroy {

  @ViewChild(DataTableDirective)
  dtElement: DataTableDirective;
  dtOptions: DataTables.Settings = {};
  dtTrigger: Subject<any> = new Subject();

  @Input() loans: Array<Loan> = null;

  ngAfterViewInit(): void {
    this.dtTrigger.next();
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

  ngOnChanges(changes: SimpleChanges): void {
    if (!changes.loans.firstChange) {
      setTimeout(() => this.rerender());
    }
  }

  rerender(): void {
    this.dtElement.dtInstance.then((dtInstance: DataTables.Api) => {
      // Destroy the table first
      dtInstance.destroy();
      // Call the dtTrigger to render again
      this.dtTrigger.next();
    });
  }

  ngOnDestroy(): void {
    // unsubscribe the event
    this.dtTrigger.unsubscribe();
  }
}
