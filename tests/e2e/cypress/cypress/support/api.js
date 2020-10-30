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

/** API call to create a document ==================================================
  * Create a document
  * :param document - the document to create
  */
 Cypress.Commands.add('apiCreateDocument', (document, titleSuffix) => {
  cy.request({
    method: 'POST',
    url: '/api/documents/',
    followRedirect: false,
    body: {
      "type": (document.type).toLowerCase(),
      "title":[{
        "type":"bf:Title",
        "mainTitle":[{
          "value": (document.title.mainTitle + titleSuffix)
        }]
      }],
      "language":[{
        "type":"bf:Language",
        "value": document.languageCode1
      }],
      "provisionActivity":[{
        "statement":[
          {
            "type":"bf:Place",
            "label":[{"value":document.provisionActivity.statement.place}]
          },
          {
            "type":"bf:Agent",
            "label":[{"value":document.provisionActivity.statement.agent}]
          },
          {
            "type":"Date",
            "label":[{"value":document.provisionActivity.statement.date}]
          }
        ],
        "type":"bf:Publication",
        "place":[{
          "type":"bf:Place",
          "country":"xx"
        }],
        "startDate": parseInt(document.provisionActivity.publicationDate1)
      }],
      "issuance":{
        "main_type":"rdami:1001",
        "subtype":"materialUnit"
      }
    }
  })
  .its('body').then((body) => {
    cy.wrap(body.id).as('getDocumentPid');
  })
  .then(() => {
    cy.get('@getDocumentPid').then((pid) => {
      cy.log('Document created, pid = ' + pid);
    });
  });
});


/** API call to create an item ==================================================
  * Create an item
  * :param resourceName - string: the resource type
  * :param query - string: criteria to find items to delete
  */
 Cypress.Commands.add('apiCreateItem', (item, barcode, documentPid) => {
  cy.request({
    method: 'POST',
    url: '/api/items/',
    followRedirect: false,
    body: {
      "acquisition_date":cy.getCurrentDate(),
      "item_type":{
        "$ref":('https://ils.rero.ch/api/item_types/' + item.itemTypePid)
      },
      "location":{
        "$ref":('https://ils.rero.ch/api/locations/' + item.locationPid)
      }
      ,"type":"standard",
      "status":"on_shelf"
      ,"barcode":barcode
      ,"call_number":barcode
      ,"document":{
        "$ref":('https://ils.rero.ch/api/documents/' + documentPid)
      }
    }
  })
  .its('body').then((body) => {
    cy.wrap(body.id).as('getItemPid');
  })
  .then(() => {
    cy.get('@getItemPid').then((pid) => {
      cy.log('Item created, pid = ' + pid);
    });
  });
});

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
        url: (['/api', resourceName, pid].join('/'))
      })
      cy.log([resourceName, '#' + pid, 'deleted'].join(' '))
    })
  })
});
