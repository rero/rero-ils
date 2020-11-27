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
  this.documentTitleSuffix = ' ' + cy.getCurrentDate();
});

describe('Example: librarian request', function() {
  // Runs once before all tests in the block
  // These steps are not part of the test, but need to be done in order to have
  // the app in the right state to run the test

  let documentPid;
  let itemPid;

  before('Login as a professional and create an item', function() {
    console.log('before');
    cy.server();
    // Login as librarian
    cy.adminLogin(this.users.librarians.spock.email, this.common.uniquePwd);
    // Create a document
    cy.apiCreateDocument(this.documents.book, this.documentTitleSuffix);
    cy.get('@getDocumentPid').then((pid) => {
      // Store document pid to re-use it later (an alias in deleted in the 'after' part of the test)
      documentPid = pid;
      // Create item
      cy.apiCreateItem(this.items.vulcanDefault, this.itemBarcode, pid);
    });
    cy.get('@getItemPid').then((pid) => {
      // Store item pid
      itemPid = pid;
    });
  });

  // Runs before each test in the block
  beforeEach('Action to perform before each test', function() {
    console.log('before each');
    // Preserve authentication information between the tests
    Cypress.Cookies.preserveOnce('session');
  });

  // Runs after each test in the block
  afterEach('Action to perform after each test', function() {
    console.log('after each');
  });

  // Run after all tests in the block
  // Is used to restore data as they were before the test
  after('Clean data: remove request, item and document', function() {
    console.log('after');
    cy.server();
    cy.route('POST', '/api/item/cancel_item_request').as('cancelRequest');
    cy.route({method: 'DELETE', url: '/api/items/*'}).as('deleteItem');
    // Go to item detail view
    cy.goToProfessionalDocumentDetailView(documentPid);
    cy.get('#item-' + this.itemBarcode + ' div a[name=barcode]').click();
    // Remove request
    cy.get('#' + this.users.patrons.james.patron.barcode + ' div [name=cancel]').click();
    cy.get('#modal-confirm-button').click();
    cy.wait('@cancelRequest');
    // Go back to document detail view
    cy.goToProfessionalDocumentDetailView(documentPid);
    // Remove item
    cy.apiDeleteResources('items', 'pid:"'+ itemPid + '"');
    // Remove document
    cy.apiDeleteResources('documents', 'pid:"'+ documentPid + '"');
    cy.logout();
  });

  // First test
  it('First test: a librarian makes a request for a patron', function() {
    console.log('first test');
    cy.route('/api/item/*/can_request?library_pid='
      + this.users.librarians.spock.libraryPid
      + '&patron_barcode='
      + this.users.patrons.james.patron.barcode)
      .as('getCanRequest');
      cy.route('POST', '/api/item/request').as('createRequest');
    // Go to document detailed view
    cy.goToProfessionalDocumentDetailView(documentPid);
    // Create a request
    cy.get('#item-' + this.itemBarcode + ' > [name=buttons] > [name=request]').click();
    cy.get('#patronBarcode').type(this.users.patrons.james.patron.barcode);
    cy.get('#pickupPid').select(this.items.vulcanDefault.pickupName);
    // Wait for the button unabled
    cy.wait('@getCanRequest');
    cy.get('#new-request-button').click();
    cy.wait('@createRequest');
    // Go to item detail view
    cy.goToItemDetailView(itemPid);
    // Check that the request has been done
    cy.get('#item-loans-requests').should('contain', this.users.patrons.james.patron.barcode);
  });

  // Second test
  it('Second test: check the request in admin patron profile view', function() {
    console.log('second test');
    // Go to patron profile view
    cy.visit('/professional/records/patrons');
    cy.get('#' + this.users.patrons.james.patron.barcode + '-loans').click();
    // Go to request tab
    cy.get('#pending-tab').click();
    // Assert that the item is requested
    cy.get('admin-main.ng-star-inserted > :nth-child(2)').should('contain', this.itemBarcode);
  });
});
