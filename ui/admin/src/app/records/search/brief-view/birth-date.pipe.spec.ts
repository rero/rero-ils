import { BirthDatePipe } from './birth-date.pipe';

describe('BirthDatePipe', () => {
  it('create an instance', () => {
    const pipe = new BirthDatePipe();
    expect(pipe).toBeTruthy();
  });
});
