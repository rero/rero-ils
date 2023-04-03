/*

RERO ILS
Copyright (C) 2019-2023 RERO

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
