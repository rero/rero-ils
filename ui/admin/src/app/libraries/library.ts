export interface OpeningHours {
  day: string;
  is_open: boolean;
  times: Array<Hours>;
}

export interface Hours {
  start_time: string;
  end_time: string;
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

  constructor(obj?: any) {
    Object.assign(this, obj);
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
}
