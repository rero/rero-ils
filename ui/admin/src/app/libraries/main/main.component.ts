import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { LibrariesService } from '../libraries.service';
import { Library } from '../library';

@Component({
  selector: 'libraries-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss']
})
export class MainComponent implements OnInit {

  public library: Library;

  private pid;

  constructor(
    private route: ActivatedRoute,
    public librariesService: LibrariesService
  ) {
    this.librariesService.currentLibrary.subscribe(
      library => { this.library = library; }
    );
  }

  ngOnInit() {
    this.route.params.subscribe(params => {
        this.pid = params.pid;
        if (params.pid !== undefined) {
          this.librariesService.loadLibrary(this.pid);
        } else {
          this.librariesService.setCurrentLibrary(new Library());
        }
    });
  }
}
