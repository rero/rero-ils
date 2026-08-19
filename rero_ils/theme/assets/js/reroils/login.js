// SPDX-FileCopyrightText: Fondation RERO+
// SPDX-License-Identifier: AGPL-3.0-or-later

import $ from 'jquery';

$('#password-show-hide-icon').on('click', function() {
  const field = $('#password');
  const type = field.prop('type');
  field.prop('type', type === 'password' ? 'text' : 'password');
});
