<template>
  <v-container class="text-center">
    <section>
      <h1 class="text-h3 text-sm-h3 py-4">Dashboard</h1>
      <p>Throughout the lab, you will gain hands-on experience with modern technology, from research-oriented retrieval components (overviewed in the Dashboard) to Docker and Dev Containers, which are frequently used in the industry.</p>
    </section>
  </v-container>
  <div>
    <v-form>
      <v-row class="justify-center mx-2">
        <v-col :cols="mobile ? '12' : '4'">
          <v-select v-model="component_types" :items="available_component_types" label="Select Types" multiple hint="Which components do you want to see?"/>
        </v-col>
        <v-col :cols="mobile ? '12' : '4'">
          <v-select v-model="focus_types" :items="available_focus_types" label="Select Your Focus" multiple hint="Which aspect should be fulfilled by a component?"/>
        </v-col>
        <v-col :cols="mobile ? '12' : '4'">
          <v-responsive min-width="220px" id="task-search">
            <v-text-field class="px-4" clearable label="Type here to filter &hellip;" prepend-inner-icon="mdi-magnify" variant="underlined" v-model="component_filter"  @input="(i:any) => filter_f(i)"/>
          </v-responsive>
        </v-col>
      </v-row>
    </v-form>
    <div>
      <v-row class="justify-center mx-2 mb-5">
        <v-col v-for="i in 6" :cols="mobile ? '12' : '2'" :key="'component-col-' + i">
          <v-row v-for="(row, index) in vectorizedComponents" :key="'component-col-' + i + '-row-' + index">
            <v-menu>
            <template v-slot:activator="{ props }">
              <v-card v-bind="props" v-if="vectorizedComponents[index][i-1] && vectorizedComponents[index][i-1]?.display_name && !vectorizedComponents[index][i-1].hide" class="ma-1 w-100 text-start" :max-width="max_width" :color="vectorizedComponents[index][i-1]?.color" variant="tonal" style="cursor: pointer;">
                <v-card-item><span class="text-h6 mb-1">{{ vectorizedComponents[index][i-1]?.display_name }}</span><span style="font-size: .7em;" v-if="vectorizedComponents[index][i-1].collapsed && vectorizedComponents[index][i-1].subItems > 0">&nbsp;&nbsp;(+&nbsp;{{ vectorizedComponents[index][i-1].subItems }})</span></v-card-item>
              </v-card>
            </template>

            <v-list>
              <v-list-item v-for="link in vectorizedComponents[index][i-1].links" :key="'component-col-' + i + '-row-' + index + '-link-' + link.href">
                <v-list-item-title><a :href="link.href" :target="link.target">{{ link.display_name }}</a></v-list-item-title>
              </v-list-item>
              <v-list-item v-if="vectorizedComponents[index][i-1].tirex_submission_id">
                <v-dialog>
                    <template v-slot:activator="{ props }">
                      <v-list-item-title v-bind="props" class="show-code-button" @click="fetch_code(index, i-1)">Show code</v-list-item-title>
                    </template>
                  <template v-slot:default="{ isActive }">
                    <v-card class="bg-grey-darken-3">
                      <v-card-text content="code">
                        <code-snippet v-if="code" :title="'Example code snippet for ' + vectorizedComponents[index][i-1]?.display_name" :code="code" expand_message=""/>
                      </v-card-text>

                      <v-card-actions>
                        <v-spacer></v-spacer>

                        <v-btn
                          text="Close code snippet"
                          @click="isActive.value = false"
                        ></v-btn>
                      </v-card-actions>
                    </v-card>
                  </template>
                </v-dialog>
              </v-list-item>
              <v-list-item v-if="!vectorizedComponents[index][i-1].collapsed && vectorizedComponents[index][i-1].subItems > 0">
                <v-list-item-title><a style="cursor: pointer;" @click="collapseItem(vectorizedComponents[index][i-1].display_name)">Collapse sub-items</a></v-list-item-title>
              </v-list-item>
              <v-list-item v-if="vectorizedComponents[index][i-1].collapsed && vectorizedComponents[index][i-1].subItems > 0">
                <v-list-item-title><a style="cursor: pointer;" @click="expandItem(vectorizedComponents[index][i-1].display_name)">Expand {{ vectorizedComponents[index][i-1].subItems }} items</a></v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
          </v-row>
        </v-col>
      </v-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDisplay } from 'vuetify'
const { mobile } = useDisplay()
</script>

<script lang="ts">
import {compareArrays, extractComponentTypesFromCurrentUrl, extractFocusTypesFromCurrentUrl, extractSearchQueryFromCurrentUrl} from '@/components/utils';
import CodeSnippet from "@/components/CodeSnippet.vue";
import all_components from '@/components/links.json'

interface Component {
  identifier: string;
  display_name: string;
  components?: Component[];
  links?: { display_name: string; href: string; target: string }[];
}

type ComponentSet = Map<string, { ancestors: string[]; children: string[] }>;

export default {
  name: "components",
  components: {CodeSnippet},
  data() {
    return {
      max_width: 1500,
      tirex_components: all_components,
      code: '',
      colors: {
        'Dataset': 'green',
        'Document processing': 'yellow-lighten-1',
        'Query processing': 'yellow-darken-4',
        'Retrieval': 'cyan-lighten-1',
        'Re-ranking': 'cyan-darken-3',
        'Evaluation': 'blue-grey-lighten-1'
      } as {
        [key: string]: string
      },
      expanded_entries: <string[]>[],
      component_filter: extractSearchQueryFromCurrentUrl(),
      component_types: compareArrays(extractComponentTypesFromCurrentUrl(), []) ? ['Code', 'TIREx', 'Tutorial'] : extractComponentTypesFromCurrentUrl(),
      available_component_types: ['Code', 'TIREx', 'Tutorial'],
      focus_types: compareArrays(extractFocusTypesFromCurrentUrl(), []) ? ['Precision', 'Recall'] : extractFocusTypesFromCurrentUrl(),
      available_focus_types: ['Precision', 'Recall'],
      refresh: 0
    }
  },
  methods: {
    // this function recursively computes the parent and child component for each element in tirex_components. used in search evaluation
    constructComponentSet(components: Component[]): ComponentSet {
      const componentSet: ComponentSet = new Map();

      function traverse(current: Component, ancestors: string[] = []) {
        const componentKey = current.display_name;

        if (!componentSet.has(componentKey)) {
          componentSet.set(componentKey, { ancestors, children: [] });
        } else {
          componentSet.get(componentKey)?.ancestors.push(...ancestors);
        }

        if (current.components && current.components.length > 0) {
          for (const child of current.components) {
            traverse(child, [componentKey, ...ancestors]);
            const childChildren = componentSet.get(child.display_name)?.children ?? [];
            componentSet.get(componentKey)?.children.push(child.display_name, ...childChildren);
          }
        }
      }

      components.forEach((component) => traverse(component));

      return componentSet;
    },
    fetch_code(index: number, i: number) {
      this.code = this.vectorizedComponents[index][i].snippet
    },
    colorOfComponent(c:string) : string {
      return this.colors[c] ?? "grey"
    },
    collapseItem(c:string) {
      this.expanded_entries = this.expanded_entries.filter(e => e != c)
    },
    expandItem(c:string) {
      this.expanded_entries.push(c)
      console.log(this.expanded_entries)
    },
    countSubItems(component:any) {
      let ret = 0

      if ('components' in component && component['components'].length > 0) {
        for (let c of component['components']) {
              ret += 1 + this.countSubItems(c)
        }
      }

      return ret
    },
    is_collapsed(component:any) {
      const isMainComponent = ['Dataset', 'Document processing', 'Query processing', 'Retrieval', 'Re-ranking', 'Evaluation'].includes(component.display_name)
      const isDesktopAndMainComponent = isMainComponent
      // const isDesktopAndMainComponent = !mobile.value && isMainComponent
      return !this.computed_expanded_entries.includes(component.display_name) &&!isDesktopAndMainComponent
    },
    filtered_sub_components(component:any) : {display_name: string, subItems: number, pos: number, links: any[], focus_type: string|undefined|null, component_type: string|undefined|null, tirex_submission_id: string|undefined|null, snippet: string|undefined|null}[] {
      let ret: {display_name: string, subItems: number, pos: number, links: any[], focus_type: string|undefined|null, component_type: string|undefined|null, tirex_submission_id: string|undefined|null, snippet: string|undefined|null}[] = []

      if (this.is_collapsed(component) || !component['components']) {
        return ret
      }

      for (let i=0; i< component['components'].length; i++) {
          const c = component['components'][i]
          ret.push({
            'display_name': c.display_name,
            'subItems': this.countSubItems(c),
            'pos': ret.length + 1,
            'links': 'links' in c ? c['links'] : null,
            'focus_type': 'focus_type' in c ? c['focus_type'] : null,
            'component_type': 'component_type' in c ? c['component_type'] : null,
            'tirex_submission_id': c['tirex_submission_id'],
            'snippet': c['snippet'] || null,
          })

          for (let sub_c of this.filtered_sub_components(c)) {
            ret.push({
              'display_name': sub_c['display_name'],
              'subItems': this.countSubItems(sub_c),
              'pos': ret.length + 1,
              'links': sub_c['links'],
              'focus_type': 'focus_type' in sub_c ? sub_c['focus_type'] : null,
              'component_type': 'component_type' in sub_c ? sub_c['component_type'] : null,
              'tirex_submission_id': sub_c['tirex_submission_id'],
              'snippet': sub_c['snippet'] || null,
            })
          }
        }

        return ret
    },
    // used in hide_component to check whether component matches selected focus or types
    matches(c: any, t:string, available:any) {
      if (!c || c[t] + '' == 'null' ||  c[t] + '' == 'undefined' || typeof c[t][Symbol.iterator] != 'function') {
        return false
      }

      for (let i of c[t]) {
        if (available.includes(i)) {
          return true
        }
      }

      return false
    },
    filter_f(f: any) {
      this.refresh++
    },
    // this function is used in the hide_component to evaluate whether a component matches a search query
    // to determine this it searches a computed map of all parent and children nodes and tries to find a match with the search string
    component_matches_search_query (elementKey: string): boolean {
        const ancestors = this.tirex_component_relationship_set.get(elementKey)?.ancestors || [];
        const children = this.tirex_component_relationship_set.get(elementKey)?.children || [];
        const filter_adjusted_for_being_empty = this.component_filter ? this.component_filter.toLowerCase() : ''
        const matchesItself = elementKey.toLowerCase().includes(filter_adjusted_for_being_empty)

        return ancestors.some((ancestor : string) => ancestor.toLowerCase().includes(filter_adjusted_for_being_empty)) || children.some((child : string) => child.toLowerCase().includes(filter_adjusted_for_being_empty)) || matchesItself;
      },

    // used in VectorizeComponents. Calculates whether a component should be hidden based on search criteria
    hide_component(c: any) : boolean {
      const component_search_is_active = this.component_types.length != 0 && this.component_types.length != this.available_component_types.length
      const focus_search_is_active = this.focus_types.length != 0 && this.focus_types.length != this.available_focus_types.length
      const text_search_is_active = this.component_filter + '' != '' || this.component_filter + '' != 'null' || this.component_filter + '' != 'undefined'
      if (!c || (!component_search_is_active && !focus_search_is_active && !text_search_is_active)) {
        return false
      }
      let component_match = !component_search_is_active || this.matches(c, 'component_type', this.component_types)
      let focus_match = !focus_search_is_active || this.matches(c, 'focus_type', this.focus_types)
      let search_match = !text_search_is_active || this.component_matches_search_query(c.display_name)

      return !component_match || !focus_match || !search_match
    },
    updateUrlToCurrentSearchCriteria() {
      this.$router.replace({name: 'components', params: {component_types: this.component_types.join(), focus_types: this.focus_types.join(), search_query: this.component_filter}})
    },
    findMatchingParents(componentSet: ComponentSet, targetKey: string): string[] {
      const lowercaseTargetKey = targetKey.toLowerCase();
      const matchingParents: string[] = [];

      for (const [key, value] of componentSet) {
        const lowercaseKey = key.toLowerCase();

        if (lowercaseKey.includes(lowercaseTargetKey) || (value.children && value.children.length > 0 && value.children.map(child => child.toLowerCase()).includes(lowercaseTargetKey))) {
          matchingParents.push(key, ...value.ancestors);
        }
      }

      return matchingParents;
    },
  },
  computed: {
    computed_expanded_entries() : string[] {
      let ret = [...this.expanded_entries];
      if(this.component_filter !== '') {
        let terms = this.findMatchingParents(this.tirex_component_relationship_set, this.component_filter)
        terms = [...new Set(terms)];
        if(terms && terms.length > 0){
          for (let i = 0; i < terms.length; i++) {
            ret = ret.concat(terms[i]);
          }
        }
      }

      return ret
    },

    // computed variable to store the map of ancestor and child nodes for all components
    tirex_component_relationship_set() : ComponentSet {
      return this.constructComponentSet(this.tirex_components)
    },

    //computes a modified view of the tirex components to display in a grid like manner.
    vectorizedComponents() {
      //initialize array of rows for each category i.e. ['Dataset', 'Document rocessing', 'Query processing', 'Retrieval', 'Re-ranking', 'Evaluation']
      let ret: [any[]] = [[{}, {}, {}, {}, {}, {}]]

      // for each category in tirex_components
      for (let i in this.tirex_components) {
        // c is an array of all components in category i
        let c = this.tirex_components[i]

        // we set row 0, aka the headers
        ret[0][i] = {'display_name': c.display_name, 'links': c.links, 'collapsed': this.is_collapsed(c), 'subItems':this.countSubItems(c), 'hide': false, 'tirex_submission_id': ''}

        // we loop through each categories subcomponents and enrich them with information needed for the grid display
        for (let subcomponent of this.filtered_sub_components(c)) {
          if (subcomponent['pos'] >= ret.length) {
            ret.push([{}, {}, {}, {}, {}, {}])
          }
          ret[subcomponent['pos']][i] = {
            'display_name': subcomponent['display_name'],
            'color': this.colorOfComponent(c.display_name),
            'subItems': subcomponent['subItems'],
            'links': subcomponent.links,
            'collapsed': this.is_collapsed(subcomponent),
            'hide': this.hide_component(subcomponent),
            'tirex_submission_id': subcomponent['tirex_submission_id'] || null,
            'snippet': subcomponent['snippet'] || null
          }
        }
      }
      return ret
    },
  },
  watch: {
    component_types(old_value, new_value) {
      this.updateUrlToCurrentSearchCriteria()
    },
    focus_types(old_value, new_value) {
      this.updateUrlToCurrentSearchCriteria()
    },
    component_filter(old_value, new_value) {
      this.updateUrlToCurrentSearchCriteria()
    }
  }
}
</script>
<style>
.show-code-button {
  cursor: pointer;
}
.show-code-button:hover {
    color: #4F81E4 /* primary color*/
  }
</style>
