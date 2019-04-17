import {
  HttpEvent,
  HttpInterceptor,
  HttpHandler,
  HttpRequest,
  HttpErrorResponse
 } from '@angular/common/http';
 import { Observable, throwError } from 'rxjs';
 import { retry, catchError } from 'rxjs/operators';
import { Router } from '@angular/router';
import { Injectable } from '@angular/core';
import { ExceptionService } from '../services/exception.service';
import { capitalize } from '../utils';
import { ResponseStatusService } from '../services/response-status.service';

@Injectable()
export class HttpErrorInterceptor implements HttpInterceptor {

  constructor(
    private exceptionService: ExceptionService,
    private router: Router,
    private responseStatusService: ResponseStatusService
  ) {}

  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(request).pipe(
        retry(1),
        catchError((error: HttpErrorResponse) => {
          if (error.status !== 200) {
            this.exceptionService.setException(
              error.status,
              capitalize(error.statusText),
              this.responseStatusService.getMessage(error.status)
            );
            this.router.navigate(['/exception'], { skipLocationChange: true });
          }

          return throwError('Error');
        })
      );
  }
 }
