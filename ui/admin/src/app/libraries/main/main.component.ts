import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { LibrariesService } from '../libraries.service';
import { Library } from '../library';

import { BrowserService } from '../../browser.service';

@Component({
  selector: 'libraries-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss']
})
export class MainComponent implements OnInit {

  public library: Library;

  private pid;

  constructor(
    private browser: BrowserService,
    private route: ActivatedRoute,
    public librariesService: LibrariesService
  ) {
    this.librariesService.currentLibrary.subscribe(
      library => this.library = library
    );
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
        this.pid = params.pid;
    });
    this.librariesService.loadLibrary(this.pid);
  }
}
