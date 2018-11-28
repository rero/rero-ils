import { InMemoryDbService } from 'angular-in-memory-web-api';

export class InMemoryLibrariesDataService implements InMemoryDbService {
  createDb() {
    const libraries = [
      {
        'id': 1,
        'pid': 1,
        '$schema': 'http://ils.test.rero.ch/schema/organisations/organisation-v0.0.1.json',
        'name': 'Bibliothèque cantonale valdôtaine, site d\'Aoste',
        'address': 'Via Challand 132, 11100 Aosta',
        'email': 'reroilstest+aoste1@gmail.com',
        'code': 'AOSTE-CANT1',
        'opening_hours': [
          {
            'day': 'monday',
            'is_open': true,
            'times': [
              {
                'end_time': '12:00',
                'start_time': '08:00'
              },
              {
                'end_time': '18:00',
                'start_time': '15:00'
              }
            ]
          },
          {
            'day': 'tuesday',
            'is_open': true,
            'times': [
              {
                'end_time': '19:00',
                'start_time': '07:00'
              }
            ]
          },
          {
            'day': 'wednesday',
            'is_open': true,
            'times': [
              {
                'end_time': '19:00',
                'start_time': '07:00'
              }
            ]
          },
          {
            'day': 'thursday',
            'is_open': true,
            'times': [
              {
                'end_time': '19:00',
                'start_time': '07:00'
              }
            ]
          },
          {
            'day': 'friday',
            'is_open': true,
            'times': [
              {
                'end_time': '19:00',
                'start_time': '07:00'
              }
            ]
          },
          {
            'day': 'saturday',
            'is_open': false,
            'times': []
          },
          {
            'day': 'sunday',
            'is_open': false,
            'times': []
          }
        ],
        'exception_dates': [
          {
            'title': 'Vacances de Noël',
            'is_open': false,
            'start_date': '2018-12-22',
            'end_date': '2019-01-06'
          },
          {
            'title': '8 février après-midi',
            'is_open': false,
            'start_date': '2019-02-08',
            'times': [{
              'start_time': '12:00',
              'end_time': '18:00'
            }]
          },
          {
            'title': 'Dimanche du livre',
            'is_open': true,
            'start_date': '2019-05-24',
            'times': [{
              'start_time': '10:00',
              'end_time': '12:00'
            },
            {
              'start_time': '13:00',
              'end_time': '16:00'
            }]
          },
          {
            'title': '1er août',
            'is_open': false,
            'start_date': '2019-08-01',
            'repeat': {
              'interval': 1,
              'period': 'yearly',
              'data': [8]
            }
          }
        ]
      },
      {
        'id': 2,
        'pid': 2,
        '$schema': 'http://ils.test.rero.ch/schema/organisations/organisation-v0.0.1.json',
        'name': 'Bibliothèque cantonale valdôtaine, site de Pont-Saint-Martin',
        'address': 'Viale Carlo Viola 93, 11026 Pont-Saint-Martin',
        'email': 'reroilstest+aoste2@gmail.com',
        'code': 'AOSTE-CANT2',
        'opening_hours': [
          {
            'day': 'monday',
            'is_open': false,
            'times': []
          },
          {
            'day': 'tuesday',
            'is_open': true,
            'times': [
              {
                'end_time': '19:00',
                'start_time': '07:00'
              }
            ]
          },
          {
            'day': 'wednesday',
            'is_open': false,
            'times': []
          },
          {
            'day': 'thursday',
            'is_open': true,
            'times': [
              {
                'end_time': '19:00',
                'start_time': '07:00'
              }
            ]
          },
          {
            'day': 'friday',
            'is_open': false,
            'times': []
          },
          {
            'day': 'saturday',
            'is_open': true,
            'times': [
              {
                'end_time': '19:00',
                'start_time': '07:00'
              }
            ]
          },
          {
            'day': 'sunday',
            'is_open': true,
            'times': [
              {
                'end_time': '19:00',
                'start_time': '07:00'
              }
            ]
          }
        ]
      }
    ];
    return {libraries};
  }
}
