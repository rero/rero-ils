require([
    'node_modules/d3/d3',
    'node_modules/angular/angular',
    'node_modules/angular-loading-bar/build/loading-bar',
    'node_modules/invenio-search-js/dist/invenio-search-js',
  ], function() {
    // When the DOM is ready bootstrap the `invenio-serach-js`

    angular.module('reroilsAppTranslations')
      .run(['gettextCatalog', function (gettextCatalog) {
         gettextCatalog.setCurrentLanguage(document.documentElement.lang);
      }]);

    angular.element(document).ready(function() {
      angular.bootstrap(
        document.getElementById("invenio-search"), [
          'angular-loading-bar', 'invenioSearch', 'reroilsAppTranslations', 'reroilsUtils'
        ]
      );
    });
});
