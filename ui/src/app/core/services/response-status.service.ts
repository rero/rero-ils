import { Injectable } from '@angular/core';
import { _ } from '../utils';

@Injectable()
export class ResponseStatusService {
  status = {
    100: _('CONTINUE'),
    101: _('SWITCHING PROTOCOLS'),
    102: _('PROCESSING'),
    103: _('EARLY HINTS'),
    200: _('OK'),
    201: _('CREATED'),
    202: _('ACCEPTED'),
    203: _('NON AUTHORITATIVE INFORMATION'),
    204: _('NO CONTENT'),
    205: _('RESET CONTENT'),
    206: _('PARTIAL CONTENT'),
    207: _('MULTI STATUS'),
    208: _('ALREADY REPORTED'),
    226: _('IM USED'),
    300: _('MULTIPLE CHOICES'),
    301: _('MOVED PERMANENTLY'),
    302: _('FOUND'),
    303: _('SEE OTHER'),
    304: _('NOT MODIFIED'),
    305: _('USE PROXY'),
    306: _('RESERVED'),
    307: _('TEMPORARY REDIRECT'),
    308: _('PERMANENTLY REDIRECT'),
    400: _('BAD REQUEST'),
    401: _('UNAUTHORIZED'),
    402: _('PAYMENT REQUIRED'),
    403: _('FORBIDDEN'),
    404: _('NOT FOUND'),
    405: _('METHOD NOT ALLOWED'),
    406: _('NOT ACCEPTABLE'),
    407: _('PROXY AUTHENTICATION REQUIRED'),
    408: _('REQUEST TIMEOUT'),
    409: _('CONFLICT'),
    410: _('GONE'),
    411: _('LENGTH REQUIRED'),
    412: _('PRECONDITION FAILED'),
    413: _('REQUEST ENTITY TOO LARGE'),
    414: _('REQUEST URI TOO LONG'),
    415: _('UNSUPPORTED MEDIA TYPE'),
    416: _('REQUESTED RANGE NOT SATISFIABLE'),
    417: _('EXPECTATION FAILED'),
    418: _('I AM A TEAPOT'),
    421: _('MISDIRECTED REQUEST'),
    422: _('UNPROCESSABLE ENTITY'),
    423: _('LOCKED'),
    424: _('FAILED DEPENDENCY'),
    425: _('TOO EARLY'),
    426: _('UPGRADE REQUIRED'),
    428: _('PRECONDITION REQUIRED'),
    429: _('TOO MANY REQUESTS'),
    431: _('REQUEST HEADER FIELDS TOO LARGE'),
    451: _('UNAVAILABLE FOR LEGAL REASONS'),
    500: _('INTERNAL SERVER ERROR'),
    501: _('NOT IMPLEMENTED'),
    502: _('BAD GATEWAY'),
    503: _('SERVICE UNAVAILABLE'),
    504: _('GATEWAY TIMEOUT'),
    505: _('VERSION NOT SUPPORTED'),
    506: _('VARIANT ALSO NEGOTIATES EXPERIMENTAL'),
    507: _('INSUFFICIENT STORAGE'),
    508: _('LOOP DETECTED'),
    510: _('NOT EXTENDED'),
    511: _('NETWORK AUTHENTICATION REQUIRED')
  };

  public getMessage(code: number) {
    if (this.status.hasOwnProperty(code)) {
      return this.status[code];
    }
    return undefined;
  }
}
