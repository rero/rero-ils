/*

RERO ILS
Copyright (C) 2019 RERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

*/

angular.module('reroThumbnails', [])
  .controller('thumbnailController', ['$scope', '$log', '$http', '$sce', function($scope, $log, $http, $sce) {
    $scope.thumbnail_url = '/static/images/icon_'+$scope.type+'.png';
    $scope.type = undefined;
    $scope.identifiers = {
      isbn: undefined
    };
    $scope.thumbnail_service_url = undefined;


    $scope.$on('thumbnail.init', thumbnailInit);
    function thumbnailInit(init, thumbnailurl, identifiers, type, config) {
      var thumbnail_service_url =  angular.fromJson(config).thumbnail_service_url;
      $scope.thumbnail_service_url = $sce.trustAsResourceUrl(thumbnail_service_url);
      $scope.type = type;
      $scope.identifiers = angular.fromJson(identifiers);
      $scope.thumbnail_url = thumbnailurl
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

    $scope.$watch(
        "thumbnailurl",
        function handleThumbnailUrl( thumbnailurl ) {
          if(thumbnailurl) {
            $scope.thumbnail_url = thumbnailurl;
          }
        },
        true
    );

    function getThumbnailUrl(identifiers) {
      var isbn = identifiers.isbn;
      if(isbn) {
        var config = {
          jsonpCallbackParam: 'callback',
          type: 'isbn',
          value: isbn,
          width: '60px',
          height: '60px'
        }
        // $log.log(angular.version);
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
      template: '<figure class="mb-0"><img class="img-responsive border border-light" ng-src="{{ thumbnail_url }}"> \
                  <figcaption class="text-center">{{ type | translate }}</figcaption> \
                 </figure>',
      link: function (scope, element, attrs) {
        scope.$broadcast(
            'thumbnail.init', attrs.thumbnailurl, attrs.identifiers, attrs.type, attrs.config
        );
    }
    };
  }]);
