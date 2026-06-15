// SPDX-FileCopyrightText: Fondation RERO+
// SPDX-License-Identifier: AGPL-3.0-or-later

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


