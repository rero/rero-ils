import { Component, OnInit } from '@angular/core';
import { ExceptionService } from '../services/exception.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-exception',
  templateUrl: './exception.component.html',
  styleUrls: ['./exception.component.scss']
})
export class ExceptionComponent implements OnInit {

  public exception = {};

  constructor(
    public exceptionService: ExceptionService,
    private router: Router
    ) {
    }

  ngOnInit() {
    if (this.exceptionService.isEmpty()) {
      this.router.navigate(['/']);
    }
    this.exception = this.exceptionService.getException();
  }

}
