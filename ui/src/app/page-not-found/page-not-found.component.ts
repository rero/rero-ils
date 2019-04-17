import { Component, OnInit } from '@angular/core';
import { ExceptionService, _, ResponseStatusService, capitalize } from '@app/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-page-not-found',
  template: '',
  styles: []
})
export class PageNotFoundComponent implements OnInit {

  constructor(
    private exceptionService: ExceptionService,
    private router: Router,
    private responseStatus: ResponseStatusService
  ) { }

  ngOnInit() {
    this.exceptionService.setException(
      404,
      capitalize(_('PAGE NOT FOUND')),
      this.responseStatus.getMessage(404)
    );
    this.router.navigate(['/exception'], { skipLocationChange: true });
  }

}
