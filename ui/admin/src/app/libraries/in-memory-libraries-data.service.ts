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
