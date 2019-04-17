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

export const capitalize = (s: string) => {
  if (typeof s !== 'string') {
    return '';
  }
  s = s.toLowerCase();
  return s.charAt(0).toUpperCase() + s.slice(1);
};
