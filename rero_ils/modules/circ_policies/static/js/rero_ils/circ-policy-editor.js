angular.module('customEditor')
  .controller('CircPolicyValidator', function($scope, $http, $window) {

    $scope.circ_policy = $scope.params.model;
    $scope.name = $scope.circ_policy.name;

    $scope.$watch('circ_policy.name', validateName);

    function validateName(newValue, oldValue, scope) {
      if(newValue) {
        var name = newValue;
        $http({
          method: 'GET',
          url: '/circ_policies/name/validate/' + name
        })
        .then(
          function successCallback(response) {
            if ($scope.name != $scope.circ_policy.name) {
              if ($scope.circ_policy.name == response.data.name) {
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
