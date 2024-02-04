#!/usr/bin/env python3
import yaml
import json

import textwrap

def flatten_tirex_components_to_id(obj, t=None):
    ret = {}

    if type(obj) != dict:
        return ret

    if 'tirex_submission_id' in obj:
        assert obj['tirex_submission_id'] not in ret
        obj['type'] = t
        ret[obj['tirex_submission_id']] = obj

    for k, v in obj.items():
        for i, j in flatten_tirex_components_to_id(v, t if t else k).items():
            ret[i] = j  

    return ret


id_to_component = flatten_tirex_components_to_id(yaml.load(open('links.yml').read(), Loader=yaml.FullLoader))

def get_snippet_to_run_components(component):
    component = id_to_component[component['tirex_submission_id']]
    component_type = component['type']
    dataset_initialization = textwrap.dedent('''
    # You can replace Robust04 with other datasets
    dataset = pt.get_dataset("irds:disks45/nocr/trec-robust-2004")
    ''').strip()
    snippet = ''

    if component_type == 'dataset':
        dataset_initialization = ''
        ir_datasets_id = component.get('ir_datasets_id')
        if ir_datasets_id:
            snippet = f'''
            dataset = pt.get_dataset('irds:{ir_datasets_id}')

            indexer = pt.IterDictIndexer('./index')
            indexref = indexer.index(dataset.get_corpus_iter())
            '''
        else:
            snippet = f'''
            def get_corpus_iter():
                # Iterate over the {component['display_name']} corpus
                corpus = ...
                for doc in corpus:
                    yield {{'docno': doc.docno, 'text': doc.content}}

            indexer = pt.IterDictIndexer('./index')
            indexref = indexer.index(get_corpus_iter())
            '''
    elif component_type == 'document_processing':
        tirex_submission_id = component.get('tirex_submission_id')
        if tirex_submission_id:
            snippet = f'''
            transformed_docs = tira.pt.transform_documents('{tirex_submission_id}', dataset)
            '''
    elif component_type == 'query_processing':
        tirex_submission_id = component.get('tirex_submission_id')
        if tirex_submission_id:
            snippet = f'''
            topics = dataset.get_topics(variant='title')
            transformed_queries = tira.pt.transform_queries('{tirex_submission_id}', topics)
            '''
    elif component_type in ('retrieval', 'reranking'):
        tirex_submission_id = component.get('tirex_submission_id')
        if tirex_submission_id:
            snippet = f'''
            run = tira.pt.from_retriever_submission('{tirex_submission_id}', dataset=dataset_id)
            '''
    elif component_type == 'dataset':
        pass
    else:
        raise ValueError(f'Component type "{component_type}" does not exist...')

    if snippet:
        snippet = textwrap.dedent(snippet).strip()

        if dataset_initialization:
            snippet = dataset_initialization + '\n' + snippet

    return snippet


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
        component['snippet'] = get_snippet_to_run_components(component)

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
