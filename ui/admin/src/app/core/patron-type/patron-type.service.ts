import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { ApiService } from '../api/api.service';

const httpOptions = {
  headers: new HttpHeaders({
    'Accept': 'application/rero+json',
    'Content-Type': 'application/json'
  })
};

@Injectable()
export class PatronTypeService {

  constructor(
    private apiService: ApiService,
    private http: HttpClient
  ) { }

  getApiEntryPointRecord(pid: string) {
    return this.apiService
      .getApiEntryPointByType('patron-type', true) + pid;
  }

  patronTypes() {
    return this.http.get(
      this.apiService.getApiEntryPointByType('patron-type'),
      httpOptions
    );
  }
}
