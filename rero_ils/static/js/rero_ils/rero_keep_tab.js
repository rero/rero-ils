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

(function ( $, window ) {
  $.fn.keeptab = function( options ) {

    var opts = $.extend( {
      tabsName: '.nav-tabs',
      localeItemName: 'navkeeptab',
      selector: '.nav-link'
    }, options );

    $(opts.tabsName).find(opts.selector).on('click', function() {
      var elementId = undefined;
      if ($(this).attr('id')) {
        elementId = '#' + $(this).attr('id');
      } else if ($(this).attr('href')) {
        elementId = $(this).attr('href')
      } else {
        window.console.log('Missing id or href.');
      }
      if (elementId) {
        localStorage.setItem(opts.localeItemName, elementId);
      }
    });

    var activeTab = localStorage.getItem(opts.localeItemName);
    if (activeTab &&  $(activeTab).length) {
      $(activeTab).tab('show');
    }
    return this;
  };
}( jQuery, window ));
