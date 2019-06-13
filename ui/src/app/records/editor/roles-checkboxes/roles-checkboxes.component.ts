import { AbstractControl } from '@angular/forms';
import { Component, Input, OnInit } from '@angular/core';
import { JsonSchemaFormService, TitleMapItem, buildTitleMap } from 'angular6-json-schema-form';
import { UserService } from '../../../user.service';

@Component({
  // tslint:disable-next-line:component-selector
  selector: 'app-roles-checkboxes',
  templateUrl: './roles-checkboxes.component.html',
  styleUrls: ['./roles-checkboxes.component.scss']
})
export class RolesCheckboxesComponent implements OnInit {
  formControl: AbstractControl;
  controlName: string;
  controlValue: any;
  controlDisabled = false;
  boundControl = false;
  options: any;
  layoutOrientation: string;
  formArray: AbstractControl;
  checkboxList: TitleMapItem[] = [];
  @Input() layoutNode: any;
  @Input() layoutIndex: number[];
  @Input() dataIndex: number[];

  constructor(
    private jsf: JsonSchemaFormService,
    private userService: UserService
  ) { }

  ngOnInit() {
    this.options = this.layoutNode.options || {};
    this.layoutOrientation = (this.layoutNode.type === 'checkboxes-inline' ||
      this.layoutNode.type === 'checkboxbuttons') ? 'horizontal' : 'vertical';
    this.jsf.initializeControl(this);
    this.checkboxList = buildTitleMap(
      this.options.titleMap || this.options.enumNames, this.options.enum, true
    );
    this.userService.loggedUser.subscribe(user => {
      if (!user.roles.some(role => role === 'system_librarian')) {
        this.checkboxList = this.checkboxList.filter(role => role.value !== 'system_librarian');
      }
    });
    if (this.boundControl) {
      const formArray = this.jsf.getFormControl(this);
      this.checkboxList.forEach(checkboxItem =>
        checkboxItem.checked = formArray.value.includes(checkboxItem.value)
      );
    }
  }

  updateValue(event) {
    for (const checkboxItem of this.checkboxList) {
      if (event.target.value === checkboxItem.value) {
        checkboxItem.checked = event.target.checked;
      }
      if (event.target.value === 'librarian' && !event.target.checked) {
        this.checkboxList.map(item => {
          if (item.value === 'system_librarian') {
            item.checked = false;
          }
        });
      }
    }
    if (this.boundControl) {
      this.jsf.updateArrayCheckboxList(this, this.checkboxList);
    }
  }
  isLibraryChecked(): boolean {
    let isChecked = false;
    this.checkboxList.map(item => {
      if (item.value === 'librarian') {
        isChecked = item.checked;
      }
    });
    return isChecked;
  }

  isDisabled(item) {
    if (item.value === 'system_librarian' && !this.isLibraryChecked()) {
      return true;
    }
    return false;
  }
}
