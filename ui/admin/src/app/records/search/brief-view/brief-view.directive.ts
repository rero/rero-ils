import { Directive, ViewContainerRef } from '@angular/core';

@Directive({
  selector: '[appBriefView]'
})
export class BriefViewDirective {

  constructor(public viewContainerRef: ViewContainerRef) { }

}
