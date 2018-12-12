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
