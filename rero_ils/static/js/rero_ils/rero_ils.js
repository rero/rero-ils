/*

RERO ILS
Copyright (C) 2019 RERO
Copyright (C) 2015-2018 CERN
Copyright (C) 2016 TIND

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.

*/

require([
  "node_modules/jquery/jquery",
  "node_modules/bootstrap/dist/js/bootstrap.bundle",
  // "node_modules/bootstrap-autohide-navbar/dist/bootstrap-autohide-navbar",
  "node_modules/angular/angular",
  "node_modules/angular-gettext/dist/angular-gettext"
], function () {

  $(document).ready(function () {

    $('[data-toggle="tooltip"]').tooltip();

    // flash messages
    $('.toast-container .toast').toast({
      delay: 5000
    }).toast('show');

    /* Enable the sticky autohide header */
    $('button.delete').on('click', function (e) {
      var next = $(this).data('next');
      $.ajax({
        url: $(this).data('delete-url'),
        type: 'DELETE',
        success: function (result) {
          window.location.replace(next);
          return false;
        },
        error: function (result, statut, error) {
          console.log('error: ', result, status, error);
        }
      });
    });

  $("#login-user").submit(function (e) {

    e.preventDefault(); // avoid to execute the actual submit of the form.

    var form = $(this);
    var url = form.attr('data-action');

    $.ajax({
      type: "POST",
      url: url,
      data: form.serialize(), // serializes the form's elements.
      success: function (data) {
        var next = getUrlParameter('next');
        window.location.replace(next? next : '/');
      },
      error: function (data) {
        var response = $.parseJSON(data.responseText);
        var alert = $("#js-alert");
        var msg = $("#js-alert span.msg").html(response.errors[0].message);
        alert.show();
      }
    });
  });

  var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = window.location.search.substring(1),
      sURLVariables = sPageURL.split('&'),
      sParameterName,
      i;

    for (i = 0; i < sURLVariables.length; i++) {
      sParameterName = sURLVariables[i].split('=');

      if (sParameterName[0] === sParam) {
        return sParameterName[1] === undefined ? true : decodeURIComponent(sParameterName[1]);
      }
    }
  };
  });
});
