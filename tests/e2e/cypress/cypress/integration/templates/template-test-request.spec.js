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

// Run once before all
// Use to load fixtures and set variable needed in all tests
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

describe('Template: librarian request', function() {
  // Run once before all tests in the block
  // These steps are not part of the test, but need to be done in order to have
  // the app in the right state to run the test
  before('Login as a professional and create an item', function() {
    console.log('before');
    Cypress.Cookies.debug(true);
    // Create server to watch api requests
    cy.server();
    // Open app on frontpage
    cy.visit('');
    // Check language and force to english
    cy.setLanguageToEnglish();
    // Login as librarian
    cy.adminLogin(this.users.librarians.spock.email, this.common.uniquePwd);
    // Create a document
    // Go to document editor
    cy.goToMenu('create-bibliographic-record-menu-frontpage');
    // Populate form with simple record
    cy.populateSimpleRecord(this.documents.book);
    //Save record
    cy.saveRecord();
    // Create an item
    cy.createItemFromDocumentDetailView(this.itemBarcode, this.items.vulcanDefault);
  });

  // Runs before each test in the block
  beforeEach('Action to perform before each test', function() {
    console.log('before each');
  });

  // Runs after each test in the block
  afterEach('Action to perform after each test', function() {
    console.log('after each');
  });

  // Run after all tests in the block
  // Is used to restore data as they were before the test
  // TODO: use token and API rest calls
  after('Clean data: remove request, item and document', function() {
    console.log('after');
    // TODO: find a way to preserve cookies (auth) and server after a test
    cy.server();
    cy.adminLogin(this.users.librarians.spock.email, this.common.uniquePwd);
    // Go to item detail view
    cy.goToProfessionalDocumentDetailView(this.itemBarcode);
    cy.get('#item-' + this.itemBarcode + ' div a[name=barcode]').click();
    // Remove request
    cy.get('#' + this.users.patrons.james.barcode + ' div [name=cancel]').click();
    cy.get('#modal-confirm-button').click();
    // Go back to document detail view and remove item
    cy.goToProfessionalDocumentDetailView(this.itemBarcode);
    cy.get('#item-' + this.itemBarcode + ' [name=buttons] > [name=delete]').click();
    cy.get('#modal-confirm-button').click();
    // Remove document
    cy.reload(); // Bug: need to reload the page to unable the remove button
    cy.deleteRecordFromDetailView();
  });

  // First test
  it('First test: a librarian makes a request for a patron', function() {
    console.log('first test');
    cy.route('/api/item/*/can_request?library_pid=' + this.users.librarians.spock.libraryPid + '&patron_barcode=' + this.users.patrons.james.barcode).as('getCanRequest');
    // Create a request
    cy.get('#item-' + this.itemBarcode + ' > [name=buttons] > [name=request]').click();
    cy.get('#patronBarcode').type(this.users.patrons.james.barcode);
    cy.get('#pickupPid').select(this.items.vulcanDefault.pickupName);
    // Wait for the button unabled
    cy.wait('@getCanRequest');
    cy.get('#new-request-button').click();
    // Go to item detail view (force = true to do it even if modal window is not already closed)
    cy.get('#item-' + this.itemBarcode + ' div a[name=barcode]').click({force:true});
    // Check that the request has been done
    cy.get('.card').should('contain', this.users.patrons.james.barcode);
    cy.logout();
  });

  // Second test
  it('Second test: check the request in admin patron profile view', function() {
    console.log('second test');
    cy.adminLogin(this.users.librarians.spock.email, this.common.uniquePwd);
    cy.goToMenu('patrons-menu-frontpage');
    cy.get('#' + this.users.patrons.james.barcode + '-loans').click();
    cy.get('#pending-tab').click();
    cy.get('admin-main.ng-star-inserted > :nth-child(2)').should('contain', this.itemBarcode);
    cy.logout();
  });
});
