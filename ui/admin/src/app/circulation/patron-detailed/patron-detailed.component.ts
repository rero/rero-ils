import { Component, OnInit, EventEmitter, Input, Output } from '@angular/core';
import { User } from '../../users';

@Component({
  selector: 'app-patron-detailed',
  templateUrl: './patron-detailed.component.html',
  styleUrls: ['./patron-detailed.component.scss']
})
export class PatronDetailedComponent implements OnInit {
  @Input() patron: User;
  @Output() clearPatron = new EventEmitter<User>();
  @Input() info: boolean;

  constructor() { }

  ngOnInit() {
  }

  clear() {
    if (this.patron) {
      this.clearPatron.emit(this.patron);
    }
  }
}
