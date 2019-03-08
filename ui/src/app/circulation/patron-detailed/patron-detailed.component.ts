import { Component, EventEmitter, Input, Output } from '@angular/core';
import { User } from '../../users';

@Component({
  selector: 'app-patron-detailed',
  templateUrl: './patron-detailed.component.html',
  styleUrls: ['./patron-detailed.component.scss']
})
export class PatronDetailedComponent {
  @Input() patron: User;
  @Output() clearPatron = new EventEmitter<User>();
  @Input() info: boolean;

  constructor() { }

  clear() {
    if (this.patron) {
      this.clearPatron.emit(this.patron);
    }
  }
}
