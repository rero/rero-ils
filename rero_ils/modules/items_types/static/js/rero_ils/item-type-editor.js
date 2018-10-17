angular.module('customEditor')
  .controller('ItemTypeValidator', function($scope, $http, $window) {

    $scope.item_type = $scope.params.model;
    $scope.name = $scope.item_type.name;

    $scope.$watch('item_type.name', validateName);

    function validateName(newValue, oldValue, scope) {
      if(newValue) {
        var name = newValue;
        $http({
          method: 'GET',
          url: '/items_types/name/validate/' + name
        })
        .then(
          function successCallback(response) {
            if ($scope.name != $scope.item_type.name) {
              if ($scope.item_type.name == response.data.name) {
                $scope.$broadcast('schemaForm.error.name','alreadyTakenMessage');
              }
            } else {
              $scope.$broadcast('schemaForm.error.name','alreadyTakenMessage', true);
            }
        });
      } else {
        $scope.$broadcast('schemaForm.error.name','alreadyTakenMessage', true);
      };
    };
  });
