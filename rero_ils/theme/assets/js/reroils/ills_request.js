// SPDX-FileCopyrightText: Fondation RERO+
// SPDX-License-Identifier: AGPL-3.0-or-later

import $ from 'jquery';

$(function() {
  $('#submit-btn').on('click', function(e) {
    e.preventDefault();
    const url = $('#source-url').val();
    if (url) {
      const wHost = window.location.host;
      const { origin, host } = new URL(url);
      if (wHost === host && url.indexOf('documents') > -1) {
        const orgData = $('#ill-public-form').data('organisation');
        if (orgData) {
          const orgs = String(orgData).split(',');
          const urlData = String(url.trim()).split('/');
          if (urlData.length > 0) {
            const pid = urlData.pop();
            const pidRegex = /^([0-9]*)/g;
            const result = pidRegex.exec(pid);
            if (result) {
              $.get(origin + '/api/holdings/?q=document.pid:' + result[0], function(data) {
                if (data['hits']['total']['value'] > 0) {
                  let existDialog = false;
                  $(data['hits']['hits']).each(function(index, element) {
                    const metadata = element['metadata'];
                    if ('organisation' in metadata) {
                      const orgPid = metadata['organisation']['pid'];
                      if (orgs.includes(orgPid) && !existDialog) {
                        existDialog = true;
                      }
                    }
                  });
                  if (existDialog) {
                    $("#ill-modal-document-exists").modal('show');
                  } else {
                    $("#ill-modal-confirmation").modal('show');
                  }
                } else {
                  $("#ill-modal-confirmation").modal('show');
                }
              });
            } else {
              $("#ill-modal-confirmation").modal('show');
            }
          } else {
            $("#ill-modal-confirmation").modal('show');
          }
        } else {
          $("#ill-modal-confirmation").modal('show');
        }
      } else {
        $("#ill-modal-confirmation").modal('show');
      }
    } else {
      $("#ill-modal-confirmation").modal('show');
    }
  });
  $('#ill-modal-confirmation-yes').on('click', function() {
    $("#ill-modal-confirmation").modal('hide');
    $("#ill-public-form").submit();
  });
  $('#ill-modal-document-exists-yes').on('click', function() {
    $("#ill-modal-document-exists").modal('hide');
    $("#ill-modal-confirmation").modal('show');
  });
});
