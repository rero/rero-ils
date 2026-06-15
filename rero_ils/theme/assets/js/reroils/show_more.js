// SPDX-FileCopyrightText: Fondation RERO+
// SPDX-License-Identifier: AGPL-3.0-or-later

import $ from 'jquery';

$('.show-more').on('click', function (event) {
  event.preventDefault();
  $(this).prev().html($(this).prev().data('show-more'))
  $(this).remove();
});
