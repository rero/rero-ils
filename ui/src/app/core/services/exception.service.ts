import { Injectable } from '@angular/core';

@Injectable()

export class ExceptionService {

  private exception: {};

  public constructor() {
    this.cleanException();
  }

  public setException(statusCode: number, statusText: string, message: string = null) {
    this.exception = {
      statusCode: statusCode,
      statusText: statusText,
      message: message
    };
  }

  public getException() {
    const output = this.exception;
    this.cleanException();
    return output;
  }

  public isEmpty() {
    return Object.entries(this.exception).length === 0;
  }

  private cleanException() {
    this.exception = {};
  }
}
