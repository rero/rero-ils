import { BrowserModule } from '@angular/platform-browser';
import { registerLocaleData } from '@angular/common';
import { NgModule, LOCALE_ID } from '@angular/core';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { BsLocaleService } from 'ngx-bootstrap/datepicker';
import { TranslateModule, TranslateLoader, TranslateService } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import { AlertModule } from 'ngx-bootstrap/alert';
import { ModalModule } from 'ngx-bootstrap/modal';
import { environment } from '../environments/environment';
import { defineLocale } from 'ngx-bootstrap/chronos';
import { deLocale, enGbLocale, frLocale, itLocale } from 'ngx-bootstrap/locale';
import localeDe from '@angular/common/locales/de';
import localeEn from '@angular/common/locales/en';
import localeFr from '@angular/common/locales/fr';
import localeIt from '@angular/common/locales/it';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

import { CoreModule } from '@app/core';
import { MylibraryComponent } from './mylibrary/mylibrary.component';
import { UserService } from './user.service';


export function HttpLoaderFactory(http: HttpClient) {
    let assets_prefix = '/';
    if (environment.production) {
      assets_prefix = '/static/js/rero_ils/admin/';
    }
    return new TranslateHttpLoader(
      http,
      assets_prefix + 'assets/i18n/',
      '.json?cacheBuster=' + environment.cacheBusterHash
    );
}


@NgModule({
  declarations: [
    AppComponent,
    MylibraryComponent
    // ConfirmWindowComponent
  ],
  imports: [
    CoreModule,
    BrowserModule,
    AppRoutingModule,
    HttpClientModule,
    ModalModule.forRoot(),
    AlertModule.forRoot(),
    TranslateModule.forRoot({
      loader: {
        provide: TranslateLoader,
        useFactory: HttpLoaderFactory,
        deps: [HttpClient]
      }
    })
  ],
  providers: [
    UserService,
    BsLocaleService,
    TranslateService,
    {
      provide: LOCALE_ID,
      deps: [TranslateService],
      useFactory: (translate) => translate.currentLang
    }
  ],
  bootstrap: [
    AppComponent
  ]
})
export class AppModule {
  languages = {
    'de': { ngx: deLocale,    angular: localeDe },
    'en': { ngx: enGbLocale,  angular: localeEn },
    'fr': { ngx: frLocale,    angular: localeFr },
    'it': { ngx: itLocale,    angular: localeIt }
  };

  constructor(
    private translate: TranslateService,
    private localeService: BsLocaleService
  ) {
      translate.setDefaultLang('en');
      for (const [key, value] of Object.entries(this.languages)) {
        defineLocale(key, value.ngx);
        registerLocaleData(value.angular, key);
      }
  }
}
