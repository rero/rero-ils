/*
 * This file is part of Invenio.
 * Copyright (C) 2016-2018 CERN.
 * Copyright (C) 2016 TIND.
 * Copyright (C) 2017-2018 RERO.
 *
 * Invenio is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License,
 * or (at your option) any later version.
 */

require([
    "node_modules/jquery/jquery",
    // "node_modules/bootstrap-sass/assets/javascripts/bootstrap",
    // "node_modules/popper.js/dist/umd/popper.js",
    "node_modules/bootstrap/dist/js/bootstrap.bundle",
    "node_modules/bootstrap-autohide-navbar/dist/bootstrap-autohide-navbar",
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
      /* Enable the sticky autohide header */

      $(function () {
        'use strict';

        $('.navbar').bootstrapAutoHideNavbar({
          disableAutoHide: false,
          delta: 5,
          duration: 250,
          shadow: false
        });
      });
    });
  });
