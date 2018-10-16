/*
 * This file is part of Invenio.
 * Copyright (C) 2016-2018 CERN.
 * Copyright (C) 2016 TIND.
 *
 * Invenio is free software; you can redistribute it and/or modify it
 * under the terms of the MIT License; see LICENSE file for more details.
 */

require([
    "node_modules/jquery/jquery",
    "node_modules/bootstrap-sass/assets/javascripts/bootstrap",
    "node_modules/bootstrap-autohide-navbar/dist/bootstrap-autohide-navbar.js",
    "node_modules/angular/angular",
    "node_modules/angular-gettext/dist/angular-gettext"
], function() {
    // angular.module("langSelector", ["gettext"])
    //     .factory("setLanguage", ["gettextCatalog", function(gettextCatalog){
    //         function setCurrentLanguage(lang) {
    //             gettextCatalog.setCurrentLanguage(lang);
    //         }
    //     }]);
    // $(document).ready(function() {
    //     $('#lang-code').on('change', function() {
    //         $('#language-code-form').submit();
    //     });
    // });
    $(document).ready(function(){
      $('[data-toggle="tooltip"]').tooltip();
  });
});
