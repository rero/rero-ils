/*

RERO ILS
Copyright (C) 2019 RERO

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

import { Component, Input, OnInit } from '@angular/core';
import { JsonSchemaFormService, buildFormGroup, getLayoutNode, JsonPointer, getControl } from 'angular6-json-schema-form';
import { FormArray } from '@angular/forms';

@Component({
  // tslint:disable-next-line:component-selector
  selector: 'app-fieldset',
  templateUrl: './fieldset.component.html',
  styleUrls: ['./fieldset.component.scss']
})
export class FieldsetComponent implements OnInit {
  options: any;
  expanded = true;
  containerType: string;
  @Input() layoutNode: any;
  @Input() layoutIndex: number[];
  @Input() dataIndex: number[];

  constructor(
    private jsf: JsonSchemaFormService
  ) { }

  get sectionTitle() {
    return this.options.notitle ? null : this.jsf.setItemTitle(this);
  }

  ngOnInit() {
    this.jsf.initializeControl(this);
    this.options = this.layoutNode.options || {};
    this.expanded = typeof this.options.expanded === 'boolean' ?
      this.options.expanded : !this.options.expandable;
    switch (this.layoutNode.type) {
      case 'fieldset': case 'array': case 'tab': case 'advancedfieldset':
      case 'authfieldset': case 'optionfieldset': case 'selectfieldset':
        this.containerType = 'fieldset';
        break;
      default: // 'div', 'flex', 'section', 'conditional', 'actions', 'tagsinput'
        this.containerType = 'div';
        break;
    }
    // patch as addItem ask for a $ref (mecanism used for the add button)
    // this.layoutNode.$ref = this.layoutNode.dataPointer;
  }

  toggleExpanded() {
    if (this.options.expandable) { this.expanded = !this.expanded; }
  }

  // Set attributes for flexbox container
  // (child attributes are set in root.component)
  getFlexAttribute(attribute: string) {
    const flexActive: boolean =
      this.layoutNode.type === 'flex' ||
      !!this.options.displayFlex ||
      this.options.display === 'flex';
    if (attribute !== 'flex' && !flexActive) { return null; }
    switch (attribute) {
      case 'is-flex':
        return flexActive;
      case 'display':
        return flexActive ? 'flex' : 'initial';
      case 'flex-direction': case 'flex-wrap':
        const index = ['flex-direction', 'flex-wrap'].indexOf(attribute);
        return (this.options['flex-flow'] || '').split(/\s+/)[index] ||
          this.options[attribute] || ['column', 'nowrap'][index];
      case 'justify-content': case 'align-items': case 'align-content':
        return this.options[attribute];
    }
  }
  removeItem(event) {
    event.preventDefault();
    const ret = this.jsf.removeItem(this);
  }

  addItem(event) {
    event.preventDefault();
    const newFormGroup = buildFormGroup(this.jsf.templateRefLibrary[this.layoutNode.dataPointer]);

    // Add the new form control to the parent formArray or formGroup
    if (!this.layoutNode.arrayItem) { // Add new array item to formArray
      return false;
    }
    const parentFormArray = (<FormArray>this.jsf.getFormControlGroup(this));
    parentFormArray.push(newFormGroup);

    // // Copy a new layoutNode from layoutRefLibrary
    const refNode = {'$ref': this.layoutNode.dataPointer};
    const newLayoutNode = getLayoutNode(refNode, this.jsf);
    newLayoutNode.arrayItem = this.layoutNode.arrayItem;
    if (this.layoutNode.arrayItemType) {
      newLayoutNode.arrayItemType = this.layoutNode.arrayItemType;
    } else {
      delete newLayoutNode.arrayItemType;
    }
    // Add the new layoutNode to the form layout at the end
    const layoutIndex =  Object.assign([], this.layoutIndex);
    layoutIndex[layoutIndex.length - 1] = parentFormArray.length - 1;
    const index = '/' + layoutIndex.join('/items/');
    JsonPointer.insert(this.jsf.layout, index, newLayoutNode);
    return true;
  }

  get canRemoveItem(): boolean {
    const itemRemovable = this.layoutNode.options.removable && this.layoutNode.arrayItem;
    if (!itemRemovable) {
      return false;
    }
    const parent = this.jsf.getParentNode(this);
    return parent.type === 'array' && this.getNumberOfItemsInParent(parent) > parent.options.minItems;
  }

  get canHideItem(): boolean {
    const parent = this.jsf.getParentNode(this);
    const nItemsInParent = this.getNumberOfItemsInParent(parent);
    return !this.canRemoveItem && nItemsInParent < 2;
  }

  get canHideMultipleItems(): boolean {
    const parent = this.jsf.getParentNode(this);
    const nItemsInParent = this.getNumberOfItemsInParent(parent);
    return !this.canRemoveItem && nItemsInParent > 1;
  }

  private getNumberOfItemsInParent(parent) {
    if (parent && parent.items) {
      return parent.items.filter(item => item.options.removable === true).length;
    }
    return 0;
  }

  get canAddItem(): boolean {
    const parent = this.jsf.getParentNode(this);
    return parent.type === 'array' && this.getNumberOfItemsInParent(parent) < parent.options.maxItems;
  }

  get rootFieldSet() {
    return JsonPointer.get(this.jsf.layout, this.jsf.getLayoutPointer(this), 0, 1);
  }

  get canHide() {
    const parent = this.jsf.getParentNode(this);
    // parent of parent
    if (this.rootFieldSet && this.rootFieldSet.options && this.rootFieldSet.options.show) {
      return true;
    }
    return false;
  }

  hide() {
    const field = this.rootFieldSet;
    field.options.show = false;
    // clear data of the removed field/subfields
    if (this.resetFormGroup(field)) {
      return;
    }
    for (const item of field.items) {
      this.resetFormGroup(item);
    }
  }

  private resetFormGroup(layoutNode) {
    if (!layoutNode.dataPointer) {
      return false;
    }
    const control = getControl(this.jsf.formGroup, layoutNode.dataPointer);
    if (!control) {
      return false;
    }
    control.reset();
    return true;
  }
}
