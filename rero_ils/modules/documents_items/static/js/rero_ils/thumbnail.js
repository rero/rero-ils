angular.module('reroThumbnails', [])
  .controller('thumbnailController', ['$scope', '$log', '$http', '$sce', function($scope, $log, $http, $sce) {
    $scope.thumbnail_url = '/static/images/icon_'+$scope.type+'.png';
    $scope.type = undefined;
    $scope.identifiers = {
      isbn: undefined
    };
    $scope.thumbnail_service_url = undefined;

    $scope.$on('thumbnail.init', thumbnailInit);
    function thumbnailInit(init, identifiers, type, config){
        var thumbnail_service_url =  angular.fromJson(config).thumbnail_service_url;
        $scope.thumbnail_service_url = $sce.trustAsResourceUrl(thumbnail_service_url);
        $scope.type = type;
        $scope.identifiers = angular.fromJson(identifiers);
    };
    $scope.$watch(
        "identifiers",
        function handleIdentifiers( identifiers ) {
          if(identifiers) {
              getThumbnailUrl(identifiers);
          }
        },
        true
    );
    function getThumbnailUrl(identifiers){
      var isbn = identifiers.isbn;
      if(isbn) {
        var config = {
            jsonpCallbackParam: 'callback',
            type: 'isbn',
            value: isbn,
            width: '60px',
            height: '60px'
        }
        $http.jsonp($scope.thumbnail_service_url, {params: config})
        .then(function(response){
            if(response.status === 200) {
              $scope.thumbnail_url = response.data.image;
            }
        });
      }
    }
  }])
  .directive('iconThumbnail', ['$log', 'gettextCatalog', function($log, gettextCatalog) {
    return {
      restrict: 'E',
      controller: "thumbnailController",
      scope: {
        type: '@'
      },
      template: '<img class="img-responsive icon-document" ng-src="{{ thumbnail_url }}"><span class="icon-document-type">{{ type | translate }}</span>',
      link: function (scope, element, attrs) {
        scope.$broadcast(
            'thumbnail.init', attrs.identifiers, attrs.type, attrs.config
        );
    }
    };
  }]);
