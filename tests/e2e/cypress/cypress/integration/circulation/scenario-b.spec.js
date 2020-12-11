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

before(function () {
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  });
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  });
  cy.fixture('documents').then(function (documents) {
    this.documents = documents;
  });
  cy.fixture('items').then(function (items) {
    this.items = items;
  });
  this.itemBarcode = 'request-' + cy.getCurrentDateAndHour();
});

describe('Circulation scenario B: standard loan with transit', function() {
  /**
   * DESCRIPTION
   *
   * 1. A patron makes a request on an item, to be picked up at other library. The item is on shelf.
   * 2. A librarian validates the request. The item goes in transit.
   * 3. The item is received at destination library and goes at desk.
   * 4. The item is checked out for patron at second library.
   * 5. The item is returned at second library. The item goes in transit.
   * 6. The item is received at owning library and goes on shelf.
   */

  let documentPid;
  let itemPid;
  let documentTitleSuffix = ' ' + cy.getCurrentDateAndHour();

  before('Login as a professional and create a document and an item', function() {
    // Login as librarian (Leonard)
    cy.adminLogin(this.users.librarians.leonard.email, this.common.uniquePwd);
    // Create a document
    cy.apiCreateDocument(this.documents.book, documentTitleSuffix);
    cy.get('@getDocumentPid').then((pid) => {
      // Store document pid to re-use it later (an alias in the 'after' part of the test)
      documentPid = pid;
      // Create item
      cy.apiCreateItem(this.items.starfleetStandardLoan, this.itemBarcode, pid);
    });
    cy.get('@getItemPid').then((pid) => {
      // Store item pid
      itemPid = pid;
    });
  });

  beforeEach('Action to perform before each test', function() {
    console.log('before each');
    cy.logout();
  });

  after('Clean data: remove item and document', function() {
    // Remove item
    cy.apiDeleteResources('items', 'pid:"'+ itemPid + '"');
    // Remove document
    cy.apiDeleteResources('documents', 'pid:"'+ documentPid + '"');
    cy.logout();
  });

  it('1. A patron makes a request', function() {
    /**
     * James makes a request on item, to be picked up at Starfleet library
     */
    // Login as patron
    cy.login(this.users.patrons.james.email, this.common.uniquePwd);
    // Search for the item
    cy.goToPublicDocumentDetailView(documentPid);
    // Request the item
    cy.get('#' + this.itemBarcode + '-dropdownMenu').click();
    // Select pickup location (force because menu can go over browser view)
    cy.get('#' + this.items.starfleetStandardLoanWithTransit.code).click({force: true});
    // Go to user profile, directly on requests-tab
    cy.visit('/global/patrons/profile');
    cy.get('#requests-tab').click();
    // Check barcode exists and that it's requested
    cy.get('#item-' + this.itemBarcode + '-call-number').should('contain', this.itemBarcode);
  });

  it('2. A librarian validates the request', function() {
    // Leonard validates James' request
    // Create server to watch api requests
    cy.intercept('POST', '/api/item/validate_request').as('validateRequest');
    // Login as librarian (Leonard)
    cy.adminLogin(this.users.librarians.leonard.email, this.common.uniquePwd);
    // Go to requests list
    cy.get('#user-services-menu').click();
    cy.get('#requests-menu').click();
    // Check that the document is present
    cy.get('#request-' + this.itemBarcode + ' [name="barcode"]').should('contain', this.itemBarcode);
    // Enter the barcode and validate
    cy.get('#search').type(this.itemBarcode).type('{enter}');
    cy.wait('@validateRequest');
    // Go to document detail view
    cy.goToProfessionalDocumentDetailView(documentPid);
    // Check that the item is in transit
    cy.get('#item-' + this.itemBarcode + ' > [name="status"]').should('contain', 'transit');
  });

  it('3. The item is received at destination library', function() {
    // Spock receives the item
    // Login as librarian
    cy.adminLogin(this.users.librarians.spock.email, this.common.uniquePwd);
    // Go to checkin view
    cy.get('#user-services-menu').click();
    cy.get('#circulation-menu').click();
    // Enter item barcode for receive
    cy.get('#search').type(this.itemBarcode).type('{enter}');
    // Check that the item has been received
    cy.get('#item-' + this.itemBarcode + ' [name="action-done"]').should('contain', 'receive');
  });

  it('4. The item is checked out for patron at second library', function() {
    // The item is returned at Starfleet library. Leonard makes the checkin
    var james = this.users.patrons.james;
    // Login as librarian
    cy.adminLogin(this.users.librarians.spock.email, this.common.uniquePwd);
    // Go to checkin view
    cy.get('#user-services-menu').click();
    cy.get('#circulation-menu').click();
    // Checkout
    cy.scanPatronBarcodeThenItemBarcode(james, this.itemBarcode)
    // Check that the checkout has been done
    cy.get('#item-' + this.itemBarcode + ' [name="action-done"] > i')
    .should('have.class', 'fa-arrow-circle-o-right')
  });

  it('5. The item is returned at second library', function() {
    // The item is returned at Vulcan library. Spock makes the checkin. The item goes in transit.
    // Login as librarian
    cy.adminLogin(this.users.librarians.spock.email, this.common.uniquePwd);
    // Go to checkin view
    cy.get('#user-services-menu').click();
    cy.get('#circulation-menu').click();
    // Checkin
    cy.scanItemBarcode(this.itemBarcode);
    // Check that the checkin has been done
    cy.get('#item-' + this.itemBarcode + ' [name="action-done"] > i')
    .should('have.class', 'fa-arrow-circle-o-down');
    // Check that the item is in transit
    cy.get('#item-' + this.itemBarcode + ' [name="circ-info"] [name="status"]')
    .should('contain', 'in transit');
  });

  it('6. The item is received at owning library', function() {
    // The item is received at Starfleet library by Leonard. The item goes on shelf.
    // Login as librarian
    cy.adminLogin(this.users.librarians.leonard.email, this.common.uniquePwd);
    // Go to checkin view
    cy.get('#user-services-menu').click();
    cy.get('#circulation-menu').click();
    // Receive
    cy.scanItemBarcode(this.itemBarcode);
    // Check that the item has been received
    cy.get('#item-' + this.itemBarcode + ' [name="action-done"]').should('contain', 'receive');
    // Check that the item is on shelf
    cy.get('#item-' + this.itemBarcode + ' [name="circ-info"] [name="status"]')
    .should('contain', 'on shelf');
  });
});
