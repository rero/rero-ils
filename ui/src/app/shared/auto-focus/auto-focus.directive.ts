/*

RERO ILS
Copyright (C) 2019 RERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

*/

import { AfterContentInit, Directive, ElementRef, Input } from '@angular/core';

@Directive({
  selector: '[autofocus]'
})

export class AutoFocusDirective implements AfterContentInit {

  @Input()
  public autofocus: boolean;
  private readonly element: HTMLElement;

  /**
   * Constructor
   * @param el: wrapper around a native element inside of a View
   */
  public constructor(private el: ElementRef) {
    this.element = el.nativeElement;
  }

  /**
   * Directive initialisation.
   */
  public ngAfterContentInit() {
    if (this.autofocus) {
      setTimeout(() => {
        this.element.focus();
      }, 200);
    }
  }

}
