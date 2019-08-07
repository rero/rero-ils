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

// import _ from 'lodash';

export function cleanDictKeys(data: any) {
  // let data = _.cloneDeep(data);
  for (const key in data) {
    if (data[key] === null || data[key] === undefined || data[key].length === 0) {
      delete data[key];
    }
  }
  return data;
}

export function _(str: string) {
  return str;
}
