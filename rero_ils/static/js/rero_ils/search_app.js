/*

This file is part of RERO ILS.
Copyright (C) 2018 RERO.

RERO ILS is free software; you can redistribute it
and/or modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of the
License, or (at your option) any later version.

RERO ILS is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with RERO ILS; if not, write to the
Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
MA 02111-1307, USA.

In applying this license, RERO does not
waive the privileges and immunities granted to it by virtue of its status
as an Intergovernmental Organization or submit itself to any jurisdiction.

*/

require([
    'node_modules/d3/d3',
    'node_modules/angular/angular',
    'node_modules/angular-loading-bar/build/loading-bar',
    'node_modules/invenio-search-js/dist/invenio-search-js',
  ], function() {
    // When the DOM is ready bootstrap the `invenio-search-js`

    angular.element(document).ready(function() {
      angular.bootstrap(
        document.getElementById("invenio-search"), [
          'angular-loading-bar',
          'invenioSearch',
          'invenioConfig',
          'reroilsAppTranslations',
          'reroilsUtils',
          'reroilsPerson',
          'reroThumbnails'
        ]
      );
    });
});
