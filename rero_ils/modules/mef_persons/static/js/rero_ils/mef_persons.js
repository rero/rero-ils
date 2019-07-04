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

angular.module('reroilsMefPerson', [])
  .controller('personController', ['$scope', function($scope) {

    $scope.person = null;

    $scope.$watch("record", function(record) {
       $scope.person = extract_source(record, $scope.config);
    });

    function extract_source(record, config) {
      var orders = config.persons_label_order;
      var language = config.language;
      data = record['metadata'];
      if (!(language in orders)) {
        language = orders['fallback'];
      }
      order = orders[language];
      order.some(function(source) {
        if (source in data) {
          dataSource = source;
          return true;
        }
      })
      return data[dataSource];
    }
  }]);
