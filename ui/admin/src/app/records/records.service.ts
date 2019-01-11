import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, map, debounceTime } from 'rxjs/operators';
import { of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class RecordsService {

  constructor(private http: HttpClient) { }

  getRecords(record_type: string, page: number = 1, size: number = 10, query: string = '') {
    const url = `/api/${record_type}/?page=${page}&size=${size}&q=${query}`;
    return this.http.get<any>(url).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
    );
  }

  getRecord(record_type: string, pid: string) {
    const url = `/api/${record_type}/${pid}`;
    return this.http.get<any>(url).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
    );
  }

  getRecordFromBNF(ean) {
    const url = `/api/import/bnf/${ean}`;
    return this.http.get<any>(url).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
    );
  }

  delete(record_type: string, pid: string) {
    const url = `/api/${record_type}/${pid}`;
    return this.http.delete<any>(url).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      })
    );
  }

  getSchema(record_type) {
    let rec_type = record_type.replace(/ies$/, 'y');
    rec_type = rec_type.replace(/s$/, '');
    const url = `/schema/${record_type}/${rec_type}-v0.0.1.json`;
    return this.http.get<any>(url).pipe(
      catchError(e => {
        if (e.status === 404) {
          return of(null);
        }
      }),
      map(data => {
        delete data['$schema'];
        return data;
      })
    );
  }

  getSchemaForm(record_type) {
    return this.http.get<any>(`/schemaform/${record_type}`);
  }

  create(record_type, record) {
    const url = `/api/${record_type}/`;
    return this.http.post(url, record);
  }

  update(record_type, record) {
    const url = `/api/${record_type}/${record.pid}`;
    return this.http.put(url, record);
  }

  valueAlreadyExists(record_type, field, value, excludePid) {
    let url = `/api/${record_type}/?size=0&q=${field}:"${value}"`;
    if (excludePid) {
      url += ` NOT pid:${excludePid}`;
    }
    return this.http.get<any>(url).pipe(
      map(res => res.hits.total),
      map(total => total ? { alreadyTakenMessage: value } : null),
      debounceTime(1000)
    );
  }
}
