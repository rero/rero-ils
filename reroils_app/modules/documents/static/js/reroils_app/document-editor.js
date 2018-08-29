angular.module('documentEditor', ['schemaForm'])
    .controller('ImportDocument', function($scope, $http, $window) {

        // to move to document
        $scope.importEanFromBnf = function() {
          var isbn = $scope.params.model.identifiers.isbn;
          var schema = $scope.params.model['$schema'];
          $http({
              method: 'GET',
                  url: '/editor/import/bnf/ean/' + isbn
              }).then(function successCallback(response) {
                  $scope.params.model = response.data.record;
                  $scope.message.type = response.data.type;
                  $scope.message.content = response.data.content;
                  $scope.message.title = response.data.title;
                  $scope.params.model['$schema'] = schema;
              }, function errorCallback(response) {
                  if (response.status === 404) {
                      $scope.message.type = response.data.type;
                      $scope.message.content = response.data.content;
                      $scope.message.title = response.data.title;
                      $scope.params.model = {'identifiers':{'isbn': isbn}};
                  } else {
                    $scope.message.type = response.data.type;
                      $scope.message.content = response.data.content;
                      $scope.message.title = response.data.title;
                      $scope.params.model = {'identifiers':{'isbn': isbn}};
                  }
                  $scope.params.model['$schema'] = schema;
          });
        }
    })
