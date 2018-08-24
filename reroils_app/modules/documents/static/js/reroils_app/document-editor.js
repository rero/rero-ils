/* This file is part of Invenio.
* Copyright (C) 2017 RERO.
*
* Invenio is free software; you can redistribute it
* and/or modify it under the terms of the GNU General Public License as
* published by the Free Software Foundation; either version 2 of the
* License, or (at your option) any later version.
*
* Invenio is distributed in the hope that it will be
* useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
* General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with Invenio; if not, write to the
* Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
* MA 02111-1307, USA.
*
* In applying this license, RERO does not
* waive the privileges and immunities granted to it by virtue of its status
* as an Intergovernmental Organization or submit itself to any jurisdiction.
*/


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
