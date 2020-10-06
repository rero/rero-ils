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
  cy.fixture('collections').then(function (collections) {
    this.collections = collections;
  });
});

describe('Collections', function() {
  /**
   * DESCRIPTION
   *
   */
  before('Login as a professional', function() {
    // Login as librarian (Leonard)
    cy.adminLogin(this.users.librarians.spock.email, this.common.uniquePwd);
  });

  beforeEach(() => {
    Cypress.Cookies.preserveOnce('session');
  });

  after('Clean data: remove collection', function() {
    // Delete collection and confirm
    cy.get('#detail-delete-button').click();
    cy.get('#modal-confirm-button').click();
    cy.logout();
  });

  it('Create a course', function() {
    let course = this.collections.course;
    // Go to collection list
    cy.get('#user-services-menu').click();
    cy.get('#collections-menu').click();
    // Click add button
    cy.get('#search-add-button').click();
    // Fill in the form
    cy.fillCollectionEditor(course);
    // Check the course
    cy.checkCollection(course);
  });

  it('Edit a collection to change it as an exhibition', function() {
    let exhibition = this.collections.exhibition;
    // Go to editor
    cy.get('#detail-edit-button').click();
    // Fill in the form
    cy.fillCollectionEditor(exhibition);
    // Check the exhibition
    cy.checkCollection(exhibition);
  });
});
