/// <reference types="Cypress" />
/*

RERO ILS
Copyright (C) 2021 RERO

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

describe('Create a document with responsibility statement', function() {
  let documentPid;
  let documentTitleSuffix = ' ' + cy.getCurrentDateAndHour();
  before('Login as a professional and create a simple document', function() {
    this.spock = this.users.librarians.spock;
    // Login as librarian
    cy.adminLogin(this.spock.email, this.common.uniquePwd);
    cy.apiCreateDocument(this.documents.book, documentTitleSuffix);
    cy.get('@getDocumentPid').then((pid) => {
      documentPid = pid;
    });
   });

  beforeEach('Preserve logged user', function() {
    // Preserve authentication information between the tests
    Cypress.Cookies.preserveOnce('session');
  });

  after('Clean data: remove document', function() {
    // Delete document
    cy.apiDeleteResources('documents', 'pid:"'+ documentPid + '"');
    cy.logout();
    cy.log('End of the test');
  });

  it('Add responsibility statement', function() {
    cy.intercept('/api/permissions/documents/' + documentPid).as('getDocPermission');
    // Go to document editor
    cy.visit('/professional/records/documents/edit/' + documentPid);
    cy.wait('@getDocPermission');
    // Remove provision activity statement
    cy.get('#provisionActivity-0-statement-remove-button').click();
    // Display responsibility statement and fill the fields
    cy.get('#add-field-8').click();
    cy.get('#responsibilityStatement-0-0').click();
    cy.get('.dropdown-item').click();
    cy.get('#responsibilityStatement-0-0-value').type(this.documents.book.responsibilityStatement[0].value);
    cy.get('#responsibilityStatement-0-0-language').select(this.documents.book.responsibilityStatement[0].language);
    // Add value (same level)
    cy.get('#responsibilityStatement-0-0-clone-button').click();
    cy.get('#responsibilityStatement-0-1-value').type(this.documents.book.responsibilityStatement[1].value);
    // Add statement
    cy.get('#responsibilityStatement-0-clone-button').click();
    cy.get('#responsibilityStatement-1-0-value').type(this.documents.book.responsibilityStatement[2].value);

    // Save
    cy.get('#editor-save-button').click();

    // Check document detail view
    cy.checkDocumentEssentialFields(this.documents.book);
    cy.get('.row > :nth-child(2)').should('contain', this.documents.book.responsibilityStatement[0].value);
    cy.get('.row > :nth-child(4)').should('contain', this.documents.book.responsibilityStatement[1].value);
    cy.get('.row > :nth-child(6)').should('contain', this.documents.book.responsibilityStatement[2].value);
  });
})
