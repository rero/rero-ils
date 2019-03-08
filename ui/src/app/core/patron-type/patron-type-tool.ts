export class PatronTypeTool {
  generatePatronTypeKey(patronTypeId: string) {
    return 'p' + patronTypeId;
  }

  getPolicyKeyLevelName(level: boolean) {
    return level ? 'library' : 'organisation';
  }
}
