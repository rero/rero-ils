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

export interface ExceptionDates {
  title: string;
  is_open: boolean;
  start_date: string;
  end_date?: string;
  times?: Array<Hours>;
  repeat?: Repeat;
}

export class Library {
  $schema: string;
  id: number;
  pid: number;
  name: string;
  email: string;
  address: string;
  code: string;
  opening_hours: Array<OpeningHours>;
  exception_dates?: Array<ExceptionDates>;

  constructor(obj?: any) {
    this.update(obj);
    this.opening_hours = this.populateTimes(this.opening_hours);
  }

  populateTimes(openinghours) {
    for (const hours in openinghours) {
      if (openinghours[hours].times.length === 0) {
        openinghours[hours].times.push({'start_time': '00:00', 'end_time': '00:00'});
      }
    }
    return openinghours;
  }

  update(obj) {
    Object.assign(this, obj);
  }

  deleteException(index) {
    this.exception_dates.splice(index, 1);
  }

  sortExceptions() {
    this.exception_dates.sort(function(a, b) {
        const keyA = new Date(a.start_date);
        const keyB = new Date(b.start_date);
        // Compare the 2 dates
        if (keyA < keyB) { return -1; }
        if (keyA > keyB) { return 1; }
        return 0;
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
