angular.module('locationEditor', ['reroilsEditor'])
    .controller('LocationValidator', function($scope, $http, $window) {

        $scope.location = $scope.params.model;

        $scope.$watch('location.code', validateCode);

        function validateCode(newValue, oldValue, scope){
            if(newValue){
                var code = newValue;
                $http({
                    method: 'GET',
                    url: '/api/locations/?q=code:' + code
                })
                .then(
                    function successCallback(response) {
                        if(response.data.hits.total > 0) {
                            if(scope.location.pid != response.data.hits.hits[0].metadata.pid) {
                                $scope.$broadcast('schemaForm.error.code','alreadyTakenMessage');
                            }
                        }
                    },
                    function errorCallback(response) {
                        $scope.$broadcast('schemaForm.error.code', 'cannotBeVerifiedMessage');
                    }
                );
            } else {
                $scope.$broadcast('schemaForm.error.code','alreadyTakenMessage', true);
            }
        };
    }
);
