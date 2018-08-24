angular.module('reroilsUtils', [])
.controller('recordController', ['$scope', function($scope) {

    record = $scope.rec;

    $scope.numberOfLocationssAvailable = function() {
        // console.log(record);
        var record = this.record;
        if(!record.metadata.hasOwnProperty('members')){
            return 0;
        }
        var locations = record.metadata.locations;
        return locations.length;
    };
}]);
