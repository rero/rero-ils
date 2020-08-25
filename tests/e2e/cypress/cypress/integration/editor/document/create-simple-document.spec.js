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

describe('Document editor', function() {
  before('Login as a professional and create an item', function() {
    this.spock = this.users.librarians.spock;
    //Open app on frontpage
    cy.visit('');
    // Check language and force to english
    cy.setLanguageToEnglish();
    // Login as librarian
    cy.adminLogin(this.spock.email, this.common.uniquePwd);
  });

  after('Clean data: remove document', function() {
    // Delete record
    cy.deleteRecordFromDetailView();
  });

  it('Creates a document with only essential fields', function() {
    // Go to document editor
    cy.goToMenu('create-bibliographic-record-menu-frontpage');
    // Populate form with simple record
    cy.populateSimpleRecord(this.documents.book);
    //Save record
    cy.saveRecord();
    // Go to description tab
    cy.get('#documents-description-tab-link').click()
    // Assert that the values are correctly displayed
    cy.checkDocumentEssentialFields(this.documents.book);
  });
})
