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
  // Run once before all
  // Use to load fixtures and set variable needed in all tests
  cy.fixture('users').then(function (users) {
    this.users = users;
  });
  cy.fixture('common').then(function (common) {
    this.common = common;
  });
  cy.fixture('patron_types').then(function (patronTypes) {
    this.patronTypes = patronTypes;
  });
  cy.fixture('cipo').then(function (cipo) {
    this.cipo = cipo;
  });
  cy.fixture('item_types').then(function (itemTypes) {
    this.itemTypes = itemTypes;
  });
  cy.fixture('items').then(function (items) {
    this.items = items;
  });
  cy.fixture('documents').then(function (documents) {
    this.documents = documents;
  });
  this.currentDate = cy.getCurrentDateAndHour();
  this.itemBarcode = 'on-site-' + this.currentDate;
  this.nameSuffix = ' ' + this.currentDate;
});

describe(`Test 'less than one day' checkout`, function() {
  let cipoPid;
  let itemTypePid;
  let documentPid;
  let itemPid;
  let patronTypePid;

  before('Login and prepare app for tests', function() {
    // Login as librarian (Leonard)
    cy.adminLogin(this.users.librarians.leonard.email, this.common.uniquePwd);
    // Create patron type
    cy.apiCreatePatronType(this.patronTypes.visitors, this.nameSuffix);
    cy.get('@getPatronTypePid').then((pid) => {
      // Store pid
      patronTypePid = pid;
      // Apply patron type to a patron
      cy.apiUpdatePatron(this.users.patrons.nyota, patronTypePid);
      // Create an item type
      cy.apiCreateItemType(this.itemTypes.on_site, this.nameSuffix);
      cy.get('@getItemTypePid').then((pid) => {
        // Store pid
        itemTypePid = pid;
        // Create 'on site' circulation policy
        cy.apiCreateCipo(this.cipo.on_site, patronTypePid, itemTypePid, this.nameSuffix);
        cy.get('@getCipoPid').then((pid) => {
          // Store pid
          cipoPid = pid;
        });
        // Create a document
        cy.apiCreateDocument(this.documents.book, this.nameSuffix);
        cy.get('@getDocumentPid').then((pid) => {
          // Store pid
          documentPid = pid;
          // Create item
          cy.apiCreateItem(this.items.starfleet_on_site, this.itemBarcode, pid, itemTypePid);
        });
        cy.get('@getItemPid').then((pid) => {
          // Store item pid
          itemPid = pid;
        });
      });
    });
  });

  beforeEach('Preserve cookies', function() {
    // Preserve authentication information between the tests
    Cypress.Cookies.preserveOnce('session');
  });

  after('Clean data', function() {
    // Remove cipo
    cy.apiDeleteResources('circ_policies', cipoPid);
    // Link patron with 'standard' patron type to allow 'visitor' patron type deletion
    cy.apiUpdatePatron(this.users.patrons.nyota, this.users.patrons.nyota.patron.type);
    // Remove patron type
    cy.apiDeleteResources('patron_types', patronTypePid);
    // Remove item
    cy.apiDeleteResources('items', 'pid:"'+ itemPid + '"');
    // Remove item type
    cy.apiDeleteResources('item_types', itemTypePid);
    // Remove document
    cy.apiDeleteResources('documents', 'pid:"'+ documentPid + '"');
    cy.logout();
  });

  it('The item cannot be requested', function() {
    // Go to document detailed view
    cy.goToProfessionalDocumentDetailView(documentPid);
    // Create a request
    cy.get('#item-' + this.itemBarcode + ' > [name=buttons] > [name=request]').click();
    cy.get('#patronBarcode').type(this.users.patrons.nyota.patron.barcode);
    cy.get('#pickupPid').select(this.items.starfleet_on_site.pickupName);
    // Assert that the circ policy doesn't allow the request
    cy.get('formly-validation-message').should('contain', 'Circulation policy disallows the operation.');
    cy.get('#new-request-button').should('be.disabled');
    cy.get('.close').click();
  });

  it('Checkout the item', function() {
    // Go to circulation view and do a checkout
    cy.get('#user-services-menu').click();
    cy.get('#circulation-menu').click();
    cy.scanPatronBarcodeThenItemBarcode(this.users.patrons.nyota, this.itemBarcode);
    cy.get('#item-' + this.itemBarcode + ' [name=circ-info').should('contain', cy.getDateDisplayed(this.currentDate, 'en', '/'));
    cy.get('#item-' + this.itemBarcode + ' [name=action-done').should('contain', this.common.itemAction.checkedOut);
  });

  it('Checkin the item', function() {
    // Checkin
    cy.scanItemBarcode(this.itemBarcode);
    // Assert that the item was checked in and that it is on shelf
    cy.get('#item-' + this.itemBarcode).should('contain', this.itemBarcode);
    cy.get('#item-' + this.itemBarcode).should('contain', this.common.itemStatus.onShelf);
    cy.get('#item-' + this.itemBarcode).should('contain', this.common.itemAction.checkedIn);
  });
});
