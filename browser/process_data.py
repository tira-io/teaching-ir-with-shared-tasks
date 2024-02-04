#!/usr/bin/env python3
import yaml
import json


def expand_links(component):
    links = [*component.get('links', [])]
    ir_datasets_id = component.get('ir_datasets_id', None)
    if ir_datasets_id:
        if '/' in ir_datasets_id:
            base = ir_datasets_id.split('/')[0]
            fragment = f'#{ir_datasets_id}'
        else:
            base = ir_datasets_id
            fragment = ''

        links.append({
            'display_name': 'ir_datasets',
            'href': f'https://ir-datasets.com/{base}.html{fragment}',
            'target': '_blank',
        })

    tirex_submission_id = component.get('tirex_submission_id', None)
    if tirex_submission_id:
        links.append({
            'display_name': 'Submission in TIREx',
            'href': f'/submissions/{tirex_submission_id}',
        })

    if links:
        component['links'] = links

    return component


def flatten_components(components):
    flattened_components = []
    for identifier, data in components.items():
        component = {'identifier': identifier, **data}

        if 'components' in component:
            component['components'] = flatten_components(data['components'])

        if 'tirex_submission_id' in data:
            component['tirex_submission_id'] = data['tirex_submission_id']

        flattened_components.append(expand_links(component))

    return flattened_components


if __name__ == '__main__':
    components = yaml.load(open('links.yml').read(), Loader=yaml.FullLoader)
    components = flatten_components(components)
    json.dump(components, open('src/components/links.json', 'w'), indent=2, sort_keys=True)
