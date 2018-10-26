angular.module('customEditor')
  .controller('LibraryValidator', function($scope, $http, $window) {

    $scope.library = $scope.params.model;

    $scope.$watch('library.code', validateCode);

    function validateCode(newValue, oldValue, scope) {
      if(newValue) {
        var code = newValue;
        $http({
          method: 'GET',
            url: '/api/libraries/?q=code:' + code
        })
        .then(
          function successCallback(response) {
            if(response.data.hits.total > 0) {
              if(scope.library.pid != response.data.hits.hits[0].metadata.pid) {
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
