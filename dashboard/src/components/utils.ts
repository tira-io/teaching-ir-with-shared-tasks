import { ref } from 'vue'


export function compareArrays (a : string[] | null, b : string[] | null) : boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

export function extractComponentTypesFromCurrentUrl() {
    const url = ref(window.location).value.href
    const to_split = 'components/'
    let component_types = null
    let component_types_array : string[] | [] = []


    if(url.includes(to_split)) {
        component_types = url.split(to_split)[1].split('/')[0].toLowerCase()

        if(component_types !== null && component_types.includes(',')) {
            component_types_array = component_types.split(',')
        }
        else {
           component_types_array = [component_types]
        }
        for(let i = 0; i < component_types_array.length; i++) {
                component_types_array[i] = component_types_array[i].charAt(0).toUpperCase() + component_types_array[i].slice(1)
                component_types_array[i] = component_types_array[i].replace( /tirex/i, 'TIREx')
            }
    }
    return compareArrays(component_types_array, []) || compareArrays(component_types_array, [''])? [] : component_types_array
}

export function extractFocusTypesFromCurrentUrl() {
    const url = ref(window.location).value.href
    const to_split : string = 'components/' + extractComponentTypesFromCurrentUrl().join() + '/'
    let focus_type = null
    let focus_types_array : string[] | [] = []

    if(url.includes(to_split)) {
        focus_type = url.split(to_split)[1].split('/')[0].toLowerCase()
       if(focus_type !== null && focus_type.includes(',')) {
            focus_types_array = focus_type.split(',')
        }
        else {
           focus_types_array = [focus_type]
        }
     for(let i = 0; i < focus_types_array.length; i++) {
                focus_types_array[i] = focus_types_array[i].charAt(0).toUpperCase() + focus_types_array[i].slice(1)
            }
    }
    return compareArrays(focus_types_array, []) || compareArrays(focus_types_array, ['']) ? [] : focus_types_array
}

export function extractSearchQueryFromCurrentUrl() {
    const url = ref(window.location).value.href
    const to_split = 'components/' + extractComponentTypesFromCurrentUrl().join() + '/' + extractFocusTypesFromCurrentUrl().join() + '/'
    let search_query = ''
    if(url.includes(to_split)) {
       search_query = url.split(to_split)[1].split('/')[0]
    }
    if(search_query !== null && search_query.includes("%20")) {
        search_query = search_query.replaceAll("%20", " ")
    }
    return search_query ? search_query.toLowerCase() : search_query
}
