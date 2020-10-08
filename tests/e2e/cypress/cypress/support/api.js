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

/** API call to logout method ============================================== */
Cypress.Commands.add('apiLogout', () => {
  cy.request({
    method: 'GET',
    url: '/signout/',
    followRedirect: false
  })
})

/** API call to login method ==================================================
  *  :param user - object: a user object from the 'users' fixtures file
  *  :param password - string: the password to log in
  */
Cypress.Commands.add('apiLogin', (user, password) => {
  cy.request('/signin')
  .its('body')
  .then(body => {
    const $html = Cypress.$(body)
    const csrf_token = $html.find('input[name=csrf_token]').val()
    cy.log(csrf_token)

    cy.request({
      method: 'POST',
      url: '/signin/',
      followRedirect: false,
      body: {
        'email': user.email,
        'password': password,
        'csrf_token': csrf_token
      }
    }).then(response => {
      cy.visit('/')
      cy.get('#logout-menu')  // raise an error if not found
    })
  })
})


/** API call to delete items ==================================================
  * Delete resource items based on a query
  * :param resourceName - string: the resource type
  * :param query - string: criteria to find items to delete
  */
Cypress.Commands.add('apiDeleteResources', (resourceName, query) => {
  const q = encodeURI('/api/'+resourceName+'/?q='+query)
  cy.request(q).its('body.hits.hits', {timeout:2000}).then(hits => {
    hits.forEach(hit => {
      const pid = hit.metadata.pid
      cy.request({
        method: 'DELETE',
        url: '/api/'+resourceName+'/'+pid
      })
      cy.log('Template#'+pid+' deleted')
    })
  })
})
