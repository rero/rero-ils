/// <reference types="Cypress" />
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
// Pull data from common.json and users.json
beforeEach(function () {
  // get users
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  });
  // get common data
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  });
  // setup application: Use a specific preview size, specific language
  cy.setup();
});

describe('Scenario B (standard loan with transit)', function () {
  // DESCRIPTION
  // ===========
  // A request is made on item of library A (AOSTE-LYCEE), on-shelf without previous requests, to be picked up at library B (AOSTE-CANT2).
  // Validated by the librarian A (Virgile) and goes in transit.
  // Received by the librarian B (Jean Dupont) and goes at desk.
  // Picked up at library B.
  // Returned on-time at the library B, goes in transit.
  // Received at library A and goes on shelf.

  let currentDate = cy.getCurrentDateAndHour();
  var barcode = currentDate + '_scenarioB';
  it('An item is created in library A (AOSTE-LYCEE)', function() {
      const virgile = this.users.librarians.virgile;
      // Login as admin
      cy.adminLogin(virgile.email, this.common.uniquePwd);
      // Create a new item
      cy.createItem(barcode, 'Standard', 'Espaces publics');
      // Check that barcode exists
      cy.get('#item-' + barcode).should('contain', barcode);

      cy.logout();
  }),
  it('A request is made on the item, to be picked up at library B (AOSTE-CANT2)', function() {
      const simonetta = this.users.patrons.simonetta;
      const locationCode = 'AOSTE-CANT2-PUB';

      // Login as normal user to request an item
      cy.login(simonetta.email, this.common.uniquePwd);
      // Search previous item
      cy.wait(1000);
      cy.goToItem(barcode);
      // Use 'request' button and choose first item from dropdown list
      cy.get('#' + barcode + '-dropdownMenu').click();
      // Click on selected pickup location (force because menu can go over browser view)
      cy.get('#' + locationCode).click({force: true});
      // Go to user profile, directly on requests tab
      cy.goToUserProfile('requests-tab');
      // Check barcode exists and that it's requested
      cy.get('#requests').should('contain', barcode);

      cy.logout();
  })
  it('The request is validated by librarian A', function () {
      const virgile = this.users.librarians.virgile;
      // Login as librarian
      cy.login(virgile.email, this.common.uniquePwd);
      // Go to requests to validate and validate request
      cy.goToMenu('requests-menu-frontpage');
      cy.get('#search').type(barcode).type('{enter}');
      // Go to document view
      cy.wait(1000);
      cy.goToItem(barcode);
      // Check that the item is in transit
      cy.wait(1000);
      cy.get('#item-' + barcode + ' > [name="status"]').should('contain', 'transit');

      cy.logout();
  });
  it('The item is received at destination library by librarian B', function () {
    const jean = this.users.librarians.jean;
    // Login as admin
    cy.adminLogin(jean.email, this.common.uniquePwd);
    // Go to checkin view
    cy.goToMenu('circulation-menu-frontpage');
    // Enter item barcode for receive
    cy.get('#search').type(barcode).type('{enter}');
    // Check that the item has been received
    cy.wait(3000);
    cy.get('#item-' + barcode + ' > .row > .col-lg-2').should('contain', 'receive');

    cy.logout();
});
  it('The item is picked up in library B', function () {
    const simonetta = this.users.patrons.simonetta;
    const jean = this.users.librarians.jean;
    // Login as admin
    cy.adminLogin(jean.email, this.common.uniquePwd);
    // Go to checkin view
    cy.goToMenu('circulation-menu-frontpage');
    // Checkout
    cy.scanPatronBarcodeThenItemBarcode(simonetta.barcode, simonetta.fullname, barcode)
    // Check that the checkout has been done
    cy.get('#item-' + barcode + ' > .row > .col-lg-2').should('contain', 'checked-out');
    // cy.logout();
  });
  it('Simonetta returns the item on time and it goes in transit', function () {
    const jean = this.users.librarians.jean;
    // Login as admin
    cy.adminLogin(jean.email, this.common.uniquePwd);
    // Go to checkin view
    cy.goToMenu('circulation-menu-frontpage');
    // Enter item barcode for checkin
    cy.get('#search').type(barcode).type('{enter}');

    cy.logout();
  });
  it('The item is received at home library and goes on shelf', function () {
    const virgile = this.users.librarians.virgile;
    // Login as admin
    cy.adminLogin(virgile.email, this.common.uniquePwd);
    // Go to checkin view
    cy.goToMenu('circulation-menu-frontpage');
    // Enter item barcode for checkin
    cy.get('#search').type(barcode).type('{enter}');

    cy.logout();
  });
});
