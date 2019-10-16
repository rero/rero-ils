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

import { TestBed } from '@angular/core/testing';

import { CirculationPolicyService } from './circulation-policy.service';
import { RouterTestingModule } from '@angular/router/testing';
import { RecordModule, CoreModule, SharedModule } from '@rero/ng-core';
import { HttpClientModule } from '@angular/common/http';

describe('CirculationPolicyService', () => {
  beforeEach(() => TestBed.configureTestingModule({
    imports: [
      RouterTestingModule,
      CoreModule,
      SharedModule,
      RecordModule,
      HttpClientModule
    ]
  }));

  it('should be created', () => {
    const service: CirculationPolicyService = TestBed.get(CirculationPolicyService);
    expect(service).toBeTruthy();
  });
});
