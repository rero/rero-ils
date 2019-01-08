require([
  'node_modules/d3/d3',
  'node_modules/angular/angular',
  'node_modules/angular-loading-bar/build/loading-bar'
  ], function() {
    // When the DOM is ready bootstrap the `invenio-serach-js`

    angular.element(document).ready(function() {
      angular.bootstrap(
        document.getElementById("thumbnail"), [
        'angular-loading-bar', 'reroilsAppTranslations', 'reroThumbnails'
        ]
        );
    });
  });