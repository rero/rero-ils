angular.module('reroilsEditor', ['schemaForm'])
  .controller('FormController', function($scope, $http, $window) {

    $scope.params = {
      form: ["*"],
      model: {},
      schema: {},
      api_save_url: '',
      parent_pid: undefined
    };

    $scope.message = {
      title:"",
      content: "",
      type: ""
    };

    function editorInit(init, form, schema, model, api_save_url, parent_pid) {
      $scope.params.schema = angular.fromJson(schema);
      $scope.params.model = angular.fromJson(model);
      $scope.params.form = angular.fromJson(form);
      $scope.params.api_save_url = api_save_url;
      $scope.params.parent_pid = parent_pid;
    };

    $scope.$on('edit.init', editorInit);

    // to move to document
    $scope.importEanFromBnf = function(test) {
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

    $scope.onSubmit = function(form) {
      // First we broadcast an event so all fields validate themselves
      $scope.$broadcast('schemaFormValidate');
      // Then we check if the form is valid
      if (form.$valid) {
        var save_url = $scope.params.api_save_url;
        var parent_pid = $scope.params.parent_pid;
        if (parent_pid !== undefined){
          save_url = save_url + '?parent_pid=' + parent_pid;
        }
        $http({
          method: 'POST',
          data: $scope.params.model,
          url: save_url
        }).then(function successCallback(response) {
          $window.location.href = response.data.next;
        }, function errorCallback(response) {
          $scope.message.type = 'danger';
          $scope.message.content = response.data.content;
          $scope.message.title = 'Error:';
        });
      }
    };

    $scope.onCancel = function() {
      window.history.back();
    }
  })

  .directive('editorParams', function($parse) {
    return {
      restrict: 'E',
      scope: false,
      controller: 'FormController',
      link: function (scope, element, attrs) {
        scope.$broadcast(
          'edit.init', attrs.form, attrs.schema, attrs.model, attrs.apiSaveUrl, attrs.parentPid
        );
      }
    }
  })

  .directive('schemaForm', function() {
    return {
      'template': '<form name="recordEditor" ng-submit="onSubmit(recordEditor)"><div sf-schema="params.schema" sf-form="params.form" sf-model="params.model"></div></form>'
    }
  })

  .directive('alert', function() {
      return {
        'template': '<div ng-show="message.title" class="alert alert-{{message.type}}"><strong>{{message.title}}</strong> {{message.content}}</div>'
      }
  });

angular.module('customEditor', ['schemaForm']);
