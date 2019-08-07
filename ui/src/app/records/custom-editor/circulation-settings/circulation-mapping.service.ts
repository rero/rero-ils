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
along with this program.  If not, see <http://www.gnu.org/licenses/>.

*/

import { Injectable } from '@angular/core';
import { PatronTypeTool, ItemTypeTool } from '@app/core';

@Injectable()
export class CirculationMappingService {

  private patronTypes = [];

  private itemTypes = [];

  private mapping = {
    organisation: {},
    library: {}
  };

  private policyLevel = 'organisation';

  constructor(
    private patronTypeTool: PatronTypeTool,
    private itemTypeTool: ItemTypeTool
  ) { }

  public generate(
    itemTypes: any,
    patronTypes: any,
    circulations: any,
    currentCirculation: any
  ) {
    const baseMapping = {};
    patronTypes.hits.hits.forEach(patronType => {
      const pkey = this.patronTypeTool.generatePatronTypeKey(patronType.metadata.pid);
      baseMapping[pkey] = {
        disabled: false,
        itemTypes: {}
      };
      itemTypes.hits.hits.forEach(itemType => {
        const iKey = this.itemTypeTool.generateItemTypeKey(itemType.metadata.pid);
        baseMapping[pkey]['itemTypes'][iKey] = false;
      });
    });
    this.mapping.organisation = JSON.parse(JSON.stringify(baseMapping));
    this.mapping.library = JSON.parse(JSON.stringify(baseMapping));

    circulations.hits.hits.forEach(circulation => {
      const data = circulation.metadata;
      if (currentCirculation.pid !== data.pid) {
        const settings = data.settings;
        if (settings) {
          const pLevel = this.translatePolicyLevel(data.policy_library_level);
          settings.forEach(setting => {
            const pKey = this.patronTypeTool.generatePatronTypeKey(setting.patron_type.pid);
            const iKey = this.itemTypeTool.generateItemTypeKey(setting.item_type.pid);
            this.mapping[pLevel][pKey]['itemTypes'][iKey] = true;
          });
        }
      }
    });

    for (const pLevel in this.mapping) {
      if (pLevel) {
        for (const pKey in this.mapping[pLevel]) {
          if (pKey) {
            let disabled = true;
            for (const iKey in this.mapping[pLevel][pKey]['itemTypes']) {
              if (!this.mapping[pLevel][pKey]['itemTypes'][iKey] && disabled) {
                disabled = false;
              }
            }
            this.mapping[pLevel][pKey]['disabled'] = disabled;
          }
        }
      }
    }

    this.patronTypes = this.serializePatronTypes(patronTypes.hits.hits);
    this.itemTypes = this.serializeItemTypes(itemTypes.hits.hits);
  }

  public getMapping() {
    return this.mapping;
  }

  public setPolicyLevel(level: boolean) {
    this.policyLevel = this.translatePolicyLevel(level);
    return this;
  }

  public getPatronTypes() {
    return this.patronTypes;
  }

  public isPatronTypeDisabled(patronTypeId: string) {
    return this.mapping[this.policyLevel][patronTypeId]['disabled'];
  }

  public getItemTypes() {
    return this.itemTypes;
  }

  public isItemTypeDisabled(patronTypeId: string, itemTypeId: string) {
    return this.mapping[this.policyLevel][patronTypeId]['itemTypes'][itemTypeId];
  }

  private translatePolicyLevel(level: boolean): string {
    return level ? 'library' : 'organisation';
  }

  private serializePatronTypes(patronTypes: any) {
    const output = [];
    patronTypes.forEach(patronType => {
      const pkey = this.patronTypeTool.generatePatronTypeKey(patronType.metadata.pid);
      output.push({ id: pkey, name: patronType.metadata.name });
    });
    return output;
  }

  private serializeItemTypes(itemTypes: any) {
    const output = [];
    itemTypes.forEach(itemType => {
      const iKey = this.itemTypeTool.generateItemTypeKey(itemType.metadata.pid);
      output.push({ id: iKey, name: itemType.metadata.name });
    });
    return output;
  }
}
