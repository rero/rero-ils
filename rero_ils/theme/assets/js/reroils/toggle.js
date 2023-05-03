/*

RERO ILS
Copyright (C) 2020 RERO

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

// Documents
$('.collapse').on('hidden.bs.collapse shown.bs.collapse', function () {
  var element = $('#' + $(this).data('holdingId')).find('.availability');
  element.hasClass('d-none') ?
    element.removeClass('d-none') : element.addClass('d-none');
});

// Patrons
$('.btn-toogle').on('click', function () {
  toogle($(this), 'target-id');
});

// ILLRequest
$('input:radio[name="copy"]').on('change', function () {
  toggleField($(this).val());
});
$('input:radio[name="copy"]:checked').trigger('change')

/**
 * Toogle element
 * @param object element
 * @param string elementId
 */
function toogle(element, elementId) {
  var target = $('#' + element.data(elementId));
  var iCaret = element.find('i');
  if (iCaret.hasClass('fa-caret-right')) {
    iCaret
      .removeClass('fa-caret-right')
      .addClass('fa-caret-down');
  } else {
    iCaret
      .removeClass('fa-caret-down')
      .addClass('fa-caret-right');
  }
  if (target.hasClass('d-none')) {
    target
      .removeClass('d-none')
      .addClass('d-block');
  } else {
    target
      .removeClass('d-block')
      .addClass('d-none');
  }
}

function toggleField(checked) {
  var target = $('div').find('[data-form-id="pages"]');
  if (checked == 0) {
    target.addClass('d-none');
  } else {
    target.removeClass('d-none');
  }
}


