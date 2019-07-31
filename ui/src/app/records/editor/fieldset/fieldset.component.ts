import { Component, Input, OnInit } from '@angular/core';
import { JsonSchemaFormService, buildFormGroup, getLayoutNode, JsonPointer } from 'angular6-json-schema-form';
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
    return this.layoutNode.options.removable && this.layoutNode.arrayItem;
  }

  get canAddItem(): boolean {
    const parent = this.jsf.getParentNode(this);
    return parent.type === 'array' && parent.items.length < parent.options.maxItems + 1;
  }
}
