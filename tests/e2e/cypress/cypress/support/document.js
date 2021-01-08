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

/** API call to create a document ==================================================
  * Create a document
  * :param document - the document to create
  * :param titleSuffix - suffix to append to the title
  */
 Cypress.Commands.add('apiCreateDocument', (document, titleSuffix) => {
  cy.request({
    method: 'POST',
    url: '/api/documents/',
    followRedirect: false,
    body: {
      "type":[{
        "main_type": document.type[0].main_type,
        "subtype": document.type[0].subtype
      }],
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
