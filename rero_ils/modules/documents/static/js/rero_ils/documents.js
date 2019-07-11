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

angular.module('reroilsUtils', [])

  .controller('exportController', ['$scope', function($scope) {
    $scope.csvURL = function() {
      return window.location.href.toString().replace('search', 'api/export/documents/csv').replace(/size=\d+/, 'size=19999');
    };
  }])

  .directive('reroilsExportCsv', function() {
    return {
      template: '<div ng-controller="exportController"><a ng-href="{{ csvURL() }}" type="button" class="btn pull-right btn-success" translate>CSV Export</a></div>'
    };
  })

  .controller('recordController', ['$scope', function($scope) {
    record = $scope.rec;
  }]);
