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
   "node_modules/bootstrap/dist/js/bootstrap.bundle",
   // "node_modules/bootstrap-autohide-navbar/dist/bootstrap-autohide-navbar",
   "node_modules/angular/angular",
   "node_modules/angular-gettext/dist/angular-gettext"
   ], function() {

    $(document).ready(function(){
      $('[data-toggle="tooltip"]').tooltip();
        $('.toast').toast({
          delay: 5000
        }).toast('show');

       /* Enable the sticky autohide header */
       $('button.delete').on('click', function (e) {
        var next = $(this).data('next');
        $.ajax({
         url: $(this).data('delete-url'),
         type: 'DELETE',
         success: function(result) {
           window.location.replace(next);
           return false;
         },
         error : function(result, statut, error){
           console.log('error: ', result, status, error);
         }
       });
      });

       // $(function () {
       //   'use strict';

       //   $('.navbar').bootstrapAutoHideNavbar({
       //     disableAutoHide: false,
       //     delta: 5,
       //     duration: 250,
       //     shadow: false
       //   });
       // });
    });
  });
