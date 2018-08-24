angular.module('patronEditor', ['reroilsEditor'])
    .controller('PatronValidator', function($scope, $http, $window) {

        $scope.patron = $scope.params.model;

        $scope.$watch('patron.barcode', validateBarcode);

        function validateBarcode(newValue, oldValue, scope){

            function validateItemBarcode(barcode){

                $http({
                    method: 'GET',
                    url: '/api/documents/?q=itemslist.barcode:' + barcode
                })
                .then(
                    function successCallback(response) {
                        if(response.data.hits.total > 0) {
                            $scope.$broadcast('schemaForm.error.barcode','alreadyTakenMessage');
                        }
                    },
                    function errorCallback(response) {
                        $scope.$broadcast('schemaForm.error.barcode', 'cannotBeVerifiedMessage');
                    }
                );
            };

            if(newValue){
                var barcode = newValue;
                $http({
                    method: 'GET',
                    url: '/api/patrons/?q=barcode:' + barcode
                })
                .then(
                    function successCallback(response) {
                        if(response.data.hits.total > 0) {
                            if(scope.patron.pid != response.data.hits.hits[0].metadata.pid) {
                                $scope.$broadcast('schemaForm.error.barcode','alreadyTakenMessage');
                            }
                            validateItemBarcode(scope.patron.barcode);
                        }
                        validateItemBarcode(scope.patron.barcode);
                    },
                    function errorCallback(response) {
                        $scope.$broadcast('schemaForm.error.barcode', 'cannotBeVerifiedMessage');
                    }
                );
            } else {
                $scope.$broadcast('schemaForm.error.barcode','alreadyTakenMessage', true);
            }
        };
    }
);
