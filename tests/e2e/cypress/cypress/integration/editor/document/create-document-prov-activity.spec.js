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

describe('Create a document with provision activity', function() {
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

  it('Add provision activity', function() {
    cy.intercept('/api/permissions/documents/' + documentPid).as('getDocPermission');
    // Go to document editor
    cy.visit('/professional/records/documents/edit/' + documentPid);
    cy.wait('@getDocPermission');
    // Add date 2
    cy.get('#provisionActivity-0').click();
    cy.get('#dropdown-basic > :nth-child(2)').click();
    cy.get('#provisionActivity-0-endDate').type(this.documents.book.provisionActivity.publicationDate2);
    // Add places
    cy.get('#provisionActivity-0-place-0-country').select(this.documents.book.provisionActivity.place);
    // Add statements
    cy.get('#provisionActivity-0-statement-0-type').select('Place');
    cy.get('#provisionActivity-0-statement-0-label-0-value').clear();
    cy.get('#provisionActivity-0-statement-0-label-0-value').type(this.documents.book.provisionActivity.statement.place);
    cy.get('#provisionActivity-0-statement-1-type').select('agent');
    cy.get('#provisionActivity-0-statement-1-label-0-value').clear();
    cy.get('#provisionActivity-0-statement-1-label-0-value').type(this.documents.book.provisionActivity.statement.agent);
    cy.get('#provisionActivity-0-statement-2-type').select('Date');
    cy.get('#provisionActivity-0-statement-2-label-0-value').clear();
    cy.get('#provisionActivity-0-statement-2-label-0-value').type(this.documents.book.provisionActivity.statement.date);
    // Save
    cy.get('#editor-save-button').click();

    // Check document detail view
    cy.checkDocumentEssentialFields(this.documents.book);
    cy.get('#doc-publication-statement-0').should('contain', this.documents.book.provisionActivity.statement.place + ' : '
      + this.documents.book.provisionActivity.statement.agent + ', '
      + this.documents.book.provisionActivity.statement.date);
  });

  it('Change provision activity', function() {
    cy.intercept('/api/permissions/documents/' + documentPid).as('getDocPermission');
    // Go to document editor
    cy.visit('/professional/records/documents/edit/' + documentPid);
    cy.wait('@getDocPermission');
    // Changes provision activity type to publication
    cy.get('#provisionActivity-0-type').select(this.documents.bookPublication.provisionActivity.type);
    // Change statements
    cy.get('#provisionActivity-0-statement-0-label-0-value').clear();
    cy.get('#provisionActivity-0-statement-0-label-0-value').type(this.documents.bookPublication.provisionActivity.statement.place1);
    cy.get('#provisionActivity-0-statement-2-clone-button').click();
    cy.get('#provisionActivity-0-statement-3-type').select('Place');
    cy.get('#provisionActivity-0-statement-3-label-0-value').type(this.documents.bookPublication.provisionActivity.statement.place2);
    // Save
    cy.get('#editor-save-button').click();

    // Check document detail view
    cy.checkDocumentEssentialFields(this.documents.bookPublication);
    cy.get('#doc-publication-statement-0').should('contain', this.documents.bookPublication.provisionActivity.statement.place1 + ' : '
      + this.documents.bookPublication.provisionActivity.statement.agent + ', '
      + this.documents.bookPublication.provisionActivity.statement.date + ' ; '
      + this.documents.bookPublication.provisionActivity.statement.place2);
  });
})
