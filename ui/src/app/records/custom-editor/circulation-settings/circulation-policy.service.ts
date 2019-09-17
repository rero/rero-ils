/*

RERO ILS
Copyright (C) 2019 RERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

*/

import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { forkJoin, of } from 'rxjs';
import { map } from 'rxjs/operators';
import { CirculationPolicy } from './circulation-policy';
import { ApiService, cleanDictKeys, _ } from '@app/core';
import { RecordsService } from '@app/records/records.service';
import { Router } from '@angular/router';
import { ToastrService } from 'ngx-toastr';

@Injectable()
export class CirculationPolicyService {

  constructor(
    private router: Router,
    private apiService: ApiService,
    private client: HttpClient,
    private recordsService: RecordsService,
    private toastService: ToastrService
  ) { }

  loadOrCreateCirculationPolicy(pid: number = null) {
    if (pid) {
      return this.recordsService.getRecord('circ_policies', '' + pid)
      .pipe(
        map(data => new CirculationPolicy(data.metadata))
      );
    } else {
      return of(new CirculationPolicy());
    }
  }

  loadAllItemTypesPatronTypesCirculationPolicies() {
    return forkJoin(
      this.recordsService.getRecords('global', 'item_types', 1, RecordsService.MAX_REST_RESULTS_SIZE),
      this.recordsService.getRecords('global', 'patron_types', 1, RecordsService.MAX_REST_RESULTS_SIZE),
      this.recordsService.getRecords('global', 'circ_policies', 1, RecordsService.MAX_REST_RESULTS_SIZE)
    );
  }

  save(circulationPolicy: CirculationPolicy) {
    circulationPolicy = cleanDictKeys(circulationPolicy);
    if (circulationPolicy.pid) {
      this.recordsService
      .update('circ_policies', circulationPolicy)
      .subscribe((circulation: any) => {
        this.toastService.success(
          _('Record Updated!'),
          _('circ_policies')
        );
        this.redirect();
      });
    } else {
      this.recordsService
      .create('circ_policies', circulationPolicy)
      .subscribe((circulation: any) => {
        this.toastService.success(
          _('Record created!'),
          _('circ_policies')
        );
        this.redirect();
      });
    }
  }

  redirect() {
    this.router.navigate(['/records/circ_policies']);
  }
}
