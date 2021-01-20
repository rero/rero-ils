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
  cy.fixture('documents').then(function (documents) {
    this.documents = documents;
  });
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  });
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  });
})

describe('Create a document', function() {
  before('Login as a professional and create an item', function() {
    this.spock = this.users.librarians.spock;
    // Login as librarian
    cy.adminLogin(this.spock.email, this.common.uniquePwd);
  });

  after('Clean data: remove document', function() {
    // Delete document
    cy.get('@documentPid').then((pid) => {
      cy.apiDeleteResources('documents', 'pid:"'+ pid + '"');
    });
    cy.logout();
    cy.log('End of the test');
  });

  it('Creates a document with only essential fields', function() {
    cy.intercept('/schemas/documents').as('documentSchemaform');
    // Go to document editor
    cy.visit('/professional/records/documents/new');
    // Populate form with simple record
    cy.wait('@documentSchemaform');
    cy.populateSimpleRecord(this.documents.book);
    //Save record
    cy.saveRecord();
    // Go to description tab
    cy.get('#documents-description-tab-link').click();
    // Get document pid for the API call in 'after' part
    cy.url().then((url) => {
      const urlParts = url.split('/');
      cy.wrap(urlParts[urlParts.length-1]).as('documentPid');
    });
    // Assert that the values are correctly displayed
    cy.checkDocumentEssentialFields(this.documents.book);
  });
})
