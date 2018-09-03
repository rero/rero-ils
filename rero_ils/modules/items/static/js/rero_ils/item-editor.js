angular.module('itemEditor', ['reroilsEditor'])
    .controller('ItemValidator', function($scope, $http, $window) {

        $scope.item = $scope.params.model;

        $scope.$watch('item.barcode', validateBarcode);

        function validateBarcode(newValue, oldValue, scope){

            function validatePatronBarcode(barcode){

                $http({
                    method: 'GET',
                    url: '/api/patrons/?q=barcode:' + barcode
                })
                .then(
                    function successCallback(response) {
                        console.log(response.data.hits.total);
                        if(response.data.hits.total > 0) {
                                $scope.$broadcast('schemaForm.error.barcode','alreadyTakenMessage');
                            };
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
                    url: '/api/documents/?q=itemslist.barcode:' + barcode
                })
                .then(
                    function successCallback(response) {
                        if(response.data.hits.total > 0) {
                            items = response.data.hits.hits[0].metadata.itemslist;
                            angular.forEach(items, function(item) {
                                if(scope.item.barcode == item.barcode) {
                                    if(scope.item.pid != item.pid) {
                                        $scope.$broadcast('schemaForm.error.barcode','alreadyTakenMessage');
                                    }
                                    validatePatronBarcode(scope.item.barcode);
                                    return;
                                }
                            });
                        }
                        validatePatronBarcode(scope.item.barcode);
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
