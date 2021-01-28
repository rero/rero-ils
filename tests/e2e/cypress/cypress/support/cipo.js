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

/** API call to create a cipo ==================================================
  * Create a circulation policy
  * :param cipo - the cipo fixture
  * :param patronTypePid - patron type pid linked to the cipo
  * :param itemTypePid - item type pid linked to the cipo
  * :param nameSuffix - suffix to append to the name
  */
 Cypress.Commands.add('apiCreateCipo', (cipo, patronTypePid, itemTypePid, nameSuffix) => {
  cy.request({
    method: 'POST',
    url: '/api/circ_policies/',
    followRedirect: false,
    body: {
      "organisation": {
        "$ref": ('https://ils.rero.ch/api/organisations/' + cipo.organisation_pid)
      },
      "name": (cipo.name + nameSuffix),
      "allow_requests": cipo.allow_requests,
      "checkout_duration": cipo.checkout_duration,
      "policy_library_level": cipo.policy_library_level,
      "is_default": cipo.is_default,
      "settings":[{
        "patron_type": {
          "$ref":('https://ils.rero.ch/api/patron_types/' + patronTypePid)
        },
        "item_type":{
          "$ref":('https://ils.rero.ch/api/item_types/' + itemTypePid)
        }
      }]
    }
  })
  .its('body').then((body) => {
    cy.wrap(body.id).as('getCipoPid');
  })
  .then(() => {
    cy.get('@getCipoPid').then((pid) => {
      cy.log('Ci-po created, pid = ' + pid);
    });
  });
});

/** UI actions to create a cipo ==================================================
  * Create a circulation policy
  * :param cipo - the cipo fixture
  * :param patronTypePid - patron type pid linked to the cipo
  * :param itemTypePid - item type pid linked to the cipo
  */
Cypress.Commands.add('uiCreateOrUpdateCipo', (cipo, patronTypePid, itemTypePid) => {
  cy.get('#name').type(cipo.name);
  cy.get('#description').type(cipo.description);
  if (!cipo.allow_checkout) {
    cy.get('input[formcontrolname="allow_checkout"]').click(); // not working
  } else {
    cy.get('#checkoutDuration').clear();
    cy.get('#checkoutDuration').type(cipo.checkout_duration);
  }
  if (!cipo.number_renewals) {
    cy.get('#renewals').check(); // not working
  } else {
    cy.get('#numberRenewals').clear();
    cy.get('#numberRenewals').type(cipo.number_renewals);
    cy.get('#renewalDuration').clear();
    cy.get('#renewalDuration').type(cipo.renewal_duration);
  }
  if (!cipo.allow_requests) {
    cy.get('#requests').check(); // not working
  }
  cy.get('#ptty-p' + patronTypePid).check();
  cy.get('#ptty-p' + patronTypePid + '-itty-i' + itemTypePid).check();
  // Save form
  cy.get('#cipo-save-button').click();
});

/** Check created circulation policy ==================================================
  * :param cipo - the cipo fixture
  * :param patronTypePid - patron type pid linked to the cipo
  * :param itemTypePid - item type pid linked to the cipo
  */
 Cypress.Commands.add('checkCipoCreated', (cipo, patronTypePid, itemTypePid) => {
  cy.get('#cipo-allow-checkout').should('have.class', 'fa-check');
  cy.get('#cipo-checkout-duration').should('contain', cipo.checkout_duration);
  cy.get('#cipo-cnumber-renewals').should('contain', cipo.number_renewals);
  cy.get('#cipo-renewal-duration').should('contain', cipo.renewal_duration);
  cy.get('#cipo-allow-request').should('have.class', 'fa-check');
  cy.get('#cipo-is-default').should('have.class', 'fa-times');
  cy.get('#cipo-after-due-date').should('contain', cipo.number_of_days_after_due_date);
  cy.get('#cipo-before-due-date').should('contain', cipo.number_of_days_before_due_date);
  cy.get('#cipo-first-reminder-fee-amount').should('contain', cipo.reminder_fee_amount);
  cy.get('#ptty-' + patronTypePid).should('contain', 'Standard');
  cy.get('#itty-' + itemTypePid).should('contain', 'Default');
  cy.get('#ptty-' + patronTypePid + '-itty-' + itemTypePid).should('have.class', 'fa-check');
});
