/*

RERO ILS
Copyright (C) 2020-2023 RERO

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

import $ from 'jquery';

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
      window.location.replace(next ? next : '/');
    },
    error: function (data) {
      var response = JSON.parse(data.responseText);
      var alert = $("#js-alert");
      var message = response.message;
      if(response.errors) {
        message = response.errors[0].message;
      }
      $("#js-alert span.msg").html(message);
      alert.show();
    }
  });
});

$('#password-show-hide').on('click', function() {
  var type = 'password' == $('#password').attr('type') ? 'text': 'password';
  $('#password').attr('type', type);
  if (type == 'text') {
    $('#password-show-hide-icon')
      .attr('title', 'Hide password')
      .removeClass('fa-eye')
      .addClass('fa-eye-slash');
  } else {
    $('#password-show-hide-icon')
      .attr('title', 'Show password')
      .removeClass('fa-eye-slash')
      .addClass('fa-eye');
  }
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
