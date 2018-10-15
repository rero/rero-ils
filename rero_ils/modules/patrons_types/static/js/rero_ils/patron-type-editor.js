angular.module('customEditor')
  .controller('PatronTypeValidator', function($scope, $http, $window) {

    $scope.patron_type = $scope.params.model;
    $scope.name = $scope.patron_type.name;

    $scope.$watch('patron_type.name', validateName);

    function validateName(newValue, oldValue, scope) {
      if(newValue) {
        var name = newValue;
        $http({
          method: 'GET',
          url: '/patrons_types/name/validate/' + name
        })
        .then(
          function successCallback(response) {
            if ($scope.name != $scope.patron_type.name) {
              if ($scope.patron_type.name == response.data.name) {
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
