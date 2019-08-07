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

import * as moment from 'moment';
import { WeekDays } from '../../../shared/week-days';

export interface OpeningHours {
  day: string;
  is_open: boolean;
  times: Array<Hours>;
}

export interface Repeat {
  interval: number;
  period: string;
  data: Array<number>;
}

export interface Hours {
  start_time: string;
  end_time: string;
}

export interface Organisation {
  $ref: string;
}

export interface ExceptionDates {
  title: string;
  is_open: boolean;
  start_date: string;
  end_date?: string;
  times?: Array<Hours>;
  repeat?: Repeat;
}

export class Library {
  $schema: string = null;
  pid: number = null;
  name: string = null;
  email: string = null;
  address: string = null;
  code: string = null;
  opening_hours: Array<OpeningHours>;
  exception_dates?: Array<ExceptionDates>;
  organisation: Organisation;

  constructor(obj?: any) {
    this.createOpeningHours();
    if (obj) {
      this.update(obj);
    }
    if (!this.exception_dates) {
      this.exception_dates = [];
    }
  }

  update(obj) {
    Object.assign(this, obj);
    this.cleanOpeningHours(this.opening_hours);
    this.reorderOpeningHours(this.opening_hours);
  }

  createOpeningHours() {
    const days = Object.keys(WeekDays);
    const openings = [];
    for (let step = 0; step < 7; step++) {
      openings.push({
        'day': days[step],
        'is_open': false,
        'times': []
      });
    }
    this.opening_hours = openings;
  }

  cleanOpeningHours(openingHours) {
    openingHours.forEach(opening => {
      const times = [];
      for (let step = 0; step < opening.times.length; step++) {
        if (
          opening.times[step].start_time !== '00:00'
          && opening.times[step].end_time !== '00:00'
        ) {
          times.push(opening.times[step]);
        }
      }
      if (times.length === 0) {
        opening.is_open = false;
      }
      opening.times = times;
    });
  }

  reorderOpeningHours(openingHours) {
    openingHours.forEach(opening => {
      if (opening.times.length > 1) {
        opening.times.sort((a, b) =>
          moment(a.start_time, 'HH:mm').diff(moment(b.start_time, 'HH:mm')));
      }
    });
  }

  deleteException(index) {
    this.exception_dates.splice(index, 1);
  }

  sortExceptions() {
    this.exception_dates.sort(function(a, b) {
      return moment(a.start_date).diff(moment(b.end_date));
    });
  }

  addException(data) {
    if (!('exception_dates' in this)) {
      this.exception_dates = [];
    }
    this.exception_dates.push(data);
    this.sortExceptions();
  }

  updateException(index, data) {
    this.exception_dates[index] = data;
  }
}
