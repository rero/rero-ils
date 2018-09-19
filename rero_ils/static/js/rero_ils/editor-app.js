(function (angular) {

    // Bootstrap it!
    angular.element(document).ready(function() {
        angular.bootstrap(
            document.getElementById("reroils-editor"), [
                'schemaForm',
                'reroilsEditor',
                'customEditor'
            ]
        );
    });
})(angular);
