import { BrowserModule } from '@angular/platform-browser';
import { LOCALE_ID, Inject, NgModule } from '@angular/core';
import { HttpClientModule, HttpClient } from '@angular/common/http';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { MylibraryComponent } from './mylibrary/mylibrary.component';

import { UserService } from './user.service';

import { TranslateModule, TranslateLoader, TranslateService } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';
import * as moment from 'moment';
import { AlertModule } from 'ngx-bootstrap/alert';
import { ModalModule } from 'ngx-bootstrap/modal';
import { environment } from '../environments/environment';

export function HttpLoaderFactory(http: HttpClient) {
    let assets_prefix = '/';
    if (environment.production) {
      assets_prefix = '/static/js/rero_ils/admin/';
    }
    return new TranslateHttpLoader(http, assets_prefix + 'assets/i18n/', '.json');
}


@NgModule({
  declarations: [
  AppComponent,
  MylibraryComponent,
  // ConfirmWindowComponent
  ],
  imports: [
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
  UserService
  ],
  bootstrap: [AppComponent]
})
export class AppModule {
  constructor(
    private translate: TranslateService,
    @Inject(LOCALE_ID) locale) {
      moment.locale(locale);
      translate.setDefaultLang('en');
      translate.use(locale);
  }
}
