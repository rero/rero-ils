// SPDX-FileCopyrightText: Fondation RERO+
// SPDX-License-Identifier: AGPL-3.0-or-later

import $ from 'jquery';

// Send a POST form only once: a double click would otherwise submit it twice.
// A jQuery handler also catches the forms sent with jQuery's submit().
$(document).on('submit', 'form[method="POST"]', function(e) {
  if ($(this).data('submitted')) {
    e.preventDefault();
    return;
  }
  $(this).data('submitted', true);
});

// Going back may restore a page whose forms were already submitted.
$(window).on('pageshow', function(e) {
  if (e.originalEvent.persisted) {
    $('form').removeData('submitted');
  }
});
