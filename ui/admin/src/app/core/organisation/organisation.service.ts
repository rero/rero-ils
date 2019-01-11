import { Injectable } from '@angular/core';
import { ApiService } from '../api/api.service';

@Injectable()
export class OrganisationService {

  constructor(
    private apiService: ApiService
  ) { }

  getApiEntryPointRecord(pid: string) {
    return this.apiService
      .getApiEntryPointByType('organisation', true) + pid;
  }
}
