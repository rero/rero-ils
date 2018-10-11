angular.module('reroilsUtils', [])
.controller('recordController', ['$scope', function($scope) {

  record = $scope.rec;

  $scope.numberOfMembersAvailable = function() {
    var record = this.record;
    if(!record.metadata.hasOwnProperty('members')) {
      return 0;
    }
    var members = record.metadata.members;
    return members.length;
  };
}]);
