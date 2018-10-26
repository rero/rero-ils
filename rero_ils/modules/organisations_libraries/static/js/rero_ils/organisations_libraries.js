angular.module('reroilsUtils', [])
.controller('recordController', ['$scope', function($scope) {

  record = $scope.rec;

  $scope.numberOfLibrariesAvailable = function() {
    var record = this.record;
    if(!record.metadata.hasOwnProperty('libraries')) {
      return 0;
    }
    var libraries = record.metadata.libraries;
    return libraries.length;
  };
}]);
