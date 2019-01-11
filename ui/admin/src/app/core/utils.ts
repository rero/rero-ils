export function cleanDictKeys(data: any) {
  for (const key in data) {
    if (data[key] === null || data[key].length === 0) {
      delete data[key];
    }
  }
  return data;
}
