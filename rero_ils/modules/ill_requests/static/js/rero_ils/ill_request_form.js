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

$(document).ready(function() {

  function toggleField(checked) {
    var target = $('div').find('[data-form-id="pages"]');
    if (checked == 0) {
      target.addClass('d-none');
    } else {
      target.removeClass('d-none');
    }
  }
  $('input:radio[name="request_copy"]').on('change', function() {
     toggleField($(this).val());
  });
  $('input:radio[name="request_copy"]:checked').trigger('change');
});
