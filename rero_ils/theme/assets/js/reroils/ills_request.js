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
along with this program. If not, see <http://www.gnu.org/licenses/>.

*/

import $ from 'jquery';

// show a confirmation modal dialog on form submission
$("#submit").on("click", function(event){
  if($(this).data('confirmed') !== true) {
    $("#ill-modal-confirmation").modal('show');
    event.preventDefault();
  }
});

// close the dialog, confirmed is true and trigger the submit click button
$("#ill-modal-confirmation-btn").on("click", function(event){
  $( "#submit" ).data('confirmed', true);
  $("#ill-modal-confirmation").modal('hide');
  // form submit does not works
  $("#submit").trigger('click');
});
