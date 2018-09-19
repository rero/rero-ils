angular.module('reroilsAppTranslations')
  .run(['gettextCatalog', function (gettextCatalog) {
     gettextCatalog.setCurrentLanguage(document.documentElement.lang);
  }]);
