// SPDX-FileCopyrightText: Fondation RERO+
// SPDX-License-Identifier: AGPL-3.0-or-later

import $ from 'jquery';

// flash messages, rendered visible by the server. Toasts kept hidden for a
// script to reveal them by id are left alone.
$('.toast-container .toast.show').toast({
  delay: 5000
}).toast('show');
