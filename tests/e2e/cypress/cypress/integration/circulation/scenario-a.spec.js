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

describe('Circulation scenario A: standard loan', function() {
  /**
   * DESCRIPTION
   *
   * 1. A patron makes a request on an item, to be picked up at ownimg library. The item is on shelf.
   * 2. A librarian validates the request. The item is at desk.
   * 3. The item is checked out for patron at owning library.
   * 4. The item is returned at owning library. Item is on shelf.
   */
  before('Login as a professional and create a document and an item', function() {
    // Create server to watch api requests
    cy.server();
    // Open app on frontpage
    cy.visit('');
    // Check language and force to english
    cy.setLanguageToEnglish();
    // Login as librarian (Leonard)
    cy.adminLogin(this.users.librarians.leonard.email, this.common.uniquePwd);
    // Create a document
    // Go to document editor
    cy.goToMenu('create-bibliographic-record-menu-frontpage');
    // Populate form with simple record
    cy.populateSimpleRecord(this.documents.book);
    //Save record
    cy.saveRecord();
    // Create an item
    cy.createItemFromDocumentDetailView(this.itemBarcode, this.items.starfleetStandardLoan);
  });

  beforeEach('Action to perform before each test', function() {
    console.log('before each');
    cy.logout();
  });

  after('Clean data: remove item and document', function() {
    // TODO: find a way to preserve cookies (auth) and server after a test
    cy.server();
    cy.route({method: 'DELETE', url: '/api/items/*'}).as('deleteItem');
    cy.adminLogin(this.users.librarians.leonard.email, this.common.uniquePwd);
    // Go to document detail view and remove item
    cy.goToProfessionalDocumentDetailView(this.itemBarcode);
    cy.get('#item-' + this.itemBarcode + ' [name=buttons] > [name=delete]').click();
    cy.get('#modal-confirm-button').click();
    cy.wait('@deleteItem');
    // Remove document
    cy.reload(); // Bug: need to reload the page to unable the remove button
    cy.deleteRecordFromDetailView();
  });

  it('1. A patron makes a request', function() {
    /**
     * James makes a request on item, to be picked up at Starfleet library.
     */
    cy.login(this.users.patrons.james.email, this.common.uniquePwd);
    // Search for the item
    cy.goToPublicDocumentDetailView(this.itemBarcode);
    // Request the item
    cy.get('#' + this.itemBarcode + '-dropdownMenu').click();
    // Select pickup location (force because menu can go over browser view)
    cy.get('#' + this.items.starfleetStandardLoan.code).click({force: true});
    // Go to user profile, directly on requests-tab
    cy.userProfile('requests-tab');
    // Check barcode exists and that it's requested
    cy.get('#item-' + this.itemBarcode + '-call-number').should('contain', this.itemBarcode);
  });

  it('2. A librarian validates the request', function() {
    /**
     * Leonard validates James' request.
     */
    cy.adminLogin(this.users.librarians.leonard.email, this.common.uniquePwd);
    // Go to requests list
    cy.goToMenu('requests-menu-frontpage')
    // Check that the document is present
    cy.get('table').should('contain', this.itemBarcode)
    // Enter the barcode and validate
    cy.get('#search').type(this.itemBarcode).type('{enter}')

    // The item should be marked as available in user profile view
    // Go to patrons list
    cy.goToMenu('patrons-menu-frontpage')
    // Go to James patron profile
    cy.get('#' + this.users.patrons.james.barcode + '-loans').click()
    // Click on tab called "To pick up"
    cy.get('#pick-up-tab').click()
    // The item should be present
    cy.get('.content').should('contain', this.itemBarcode)
  });

  it('3. The item is checked out for patron at owning library', function() {
    /**
     * Leonard checks the item out for James in Starfleet library.
     */
    cy.adminLogin(this.users.librarians.leonard.email, this.common.uniquePwd);
    // Go to circulation search bar
    cy.goToMenu('circulation-menu-frontpage');
    // Checkout
    cy.scanPatronBarcodeThenItemBarcode(this.users.patrons.james, this.itemBarcode);
    // Item barcode should be present
    cy.get('#item-' + this.itemBarcode).should('contain', this.itemBarcode);
  });

  it('4. The item is returned at owning library', function() {
    /**
     * The item is returned at Starfleet library and goes on shelf.
     * Leonard makes the checkin.
     */
    cy.adminLogin(this.users.librarians.leonard.email, this.common.uniquePwd);
    // Go to circulation search bar
    cy.goToMenu('circulation-menu-frontpage');
    // Checkin
    cy.scanItemBarcode(this.itemBarcode);
    // CHeck that the item was checked in and that it is on shelf
    cy.get('#item-' + this.itemBarcode).should('contain', this.itemBarcode);
    cy.get('#item-' + this.itemBarcode).should('contain', 'on shelf');
    cy.get('#item-' + this.itemBarcode).should('contain', 'checked in');
    cy.logout();
  });
});
