import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { forkJoin, of } from 'rxjs';
import { map } from 'rxjs/operators';
import { CirculationPolicy } from './circulation-policy';
import { ItemTypeService, PatronTypeService, ApiService, cleanDictKeys } from '@app/core';
import { RecordsService } from '@app/records/records.service';
import { Router } from '@angular/router';

const httpOptions = {
  headers: new HttpHeaders({
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  })
};

@Injectable()
export class CirculationPolicyService {

  constructor(
    private router: Router,
    private apiService: ApiService,
    private client: HttpClient,
    private itemTypeService: ItemTypeService,
    private patronTypeService: PatronTypeService,
    private recordsService: RecordsService
  ) { }

  loadOrCreateCirculationPolicy(pid: number = null) {
    if (pid) {
      return this.client.get<any>(
        this.apiService.getApiEntryPointByType('circ_policies') + pid,
        httpOptions
      ).pipe(
        map(data => new CirculationPolicy(data.metadata))
      );
    } else {
      return of(new CirculationPolicy());
    }
  }

  loadAllCirculationPolicy() {
    return this.client.get(
      this.apiService.getApiEntryPointByType('circ_policies'),
      httpOptions
    );
  }

  loadAllItemTypesPatronTypesCirculationPolicies() {
    return forkJoin(
      this.itemTypeService.itemTypes(),
      this.patronTypeService.patronTypes(),
      this.loadAllCirculationPolicy()
    );
  }

  save(circulationPolicy: CirculationPolicy) {
    circulationPolicy = cleanDictKeys(circulationPolicy);
    if (circulationPolicy.pid) {
      this.recordsService
      .update('circ_policies', circulationPolicy)
      .subscribe((circulation: any) => {
        this.redirect();
      });
    } else {
      this.recordsService
      .create('circ_policies', circulationPolicy)
      .subscribe((circulation: any) => {
        this.redirect();
      });
    }
  }

  redirect() {
    this.router.navigate(['/records/circ_policies']);
  }
}
