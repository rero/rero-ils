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
  cy.fixture('document').then(function (documentData) {
    this.document = documentData;
  });
  cy.fixture('users').then(function (userData) {
    this.users = userData;
  });
  cy.fixture('common').then(function (commonData) {
    this.common = commonData;
  });
})

describe('Document editor', function() {
  it('Creates a document with only essential fields', function() {
    const document = this.document.completeDocument;

    // Go to frontpage and log in as system librarian
    cy.setup();
    cy.adminLogin(this.users.sysLibrarians.astrid.email, this.common.uniquePwd);

    // Go to document editor
    cy.goToMenu('create-bibliographic-record-menu-frontpage');

    // Populate form with simple record
    cy.populateSimpleRecord(document);

    //Save record
    cy.saveRecord();

    // Go to description tab
    cy.get('#documents-description-tab-link').click()

    // Assert that the values are correctly displayed
    cy.checkDocumentEssentialFields(document);

    // Delete record
    cy.deleteRecordFromDetailView();
  });
})
