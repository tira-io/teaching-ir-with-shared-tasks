import {ref} from 'vue'

export async function execute_get(url: string, range: string): Promise<any> {
	if (!url.startsWith('http')) {
		url = '/' + url

		if (process.env.NODE_ENV !== 'development') {
			url = '/ir-lab-ws-23' + url
		}
	}

	const response = await fetch(url, {
		method: 'GET',
		headers: {'Range': 'bytes=' + range},
	})

	if (!response.ok) {
		throw new Error(`Error fetching endpoint: ${url} with ${response.status}`);
	}

	return await response.json()
}

function inject_response(response: any, request: any, obj: any): void {
	if (response != null) {
		obj.$data['cache'][request['path']][request['start'] + '-' + request['end']] = response
	}
}

export async function get(request: any, obj: any): Promise<any> {
	let range = request['start'] + '-' + request['end']

	if (obj.$data['cache'][request['path']][range]) {
		return obj.$data['cache'][request['path']][range]
	}

	const response = await execute_get(request['path'], range);

	inject_response(response, request, obj);
	return response;
}

export function updateUrl(topic: string|null = null, dataset: string|null = null, query: string|null = null, doc_ids: string|null = null) {
    var loc = (ref(window.location).value.href + '?').split('?')[0]
    var params = []

    if (topic != null && topic != '') {
        params.push('topic=' + topic)
    }

    if (dataset != null && dataset != '') {
        params.push('dataset=' + dataset)
    }

    if (query != null && query != '') {
        params.push('query=' + query)
    }

    if (doc_ids != null && doc_ids != '') {
        params.push('doc_ids=' + doc_ids)
    }

    let ret = params.length == 0 ? loc : loc + '?' + params.join('&')
    history.replaceState({'url': ret}, 'ir_datasets explorer', ret)

    return ret
}

export function extractFromUrl(param: string, default_value: string | null = null): string | null {
    let href = (ref(window.location).value.href + '&')

    if (href.indexOf(param + '=') === -1) {
        return default_value;
    }

    return decodeURI(href.split(param + '=')[1].split('&')[0]);
}

export function uniqueElements(elements: any[], key: string) {
	return [...new Set(elements.map(i => i[key]))]
}

export function filter_topics(topics: {query_id: string, dataset: string, default_text: string}[], topic_num_filters: string | null = null, dataset_filters: string | null = null, query_filter: string | null = null): {query_id: string, dataset: string, default_text: string}[] {
	let ret: {query_id: string, dataset: string, default_text: string}[] = []

	for (let topic of topics) {
		let match_topic_num_filters = topic_num_filters == null || topic_num_filters == '' || ('' + topic_num_filters).split(',').some(i => i && i == topic.query_id)

		let match_dataset_filters = dataset_filters == null || dataset_filters == '' || ('' + dataset_filters).split(',').some(i => i && i == topic.dataset)

		let match_query_filter = !query_filter || topic.default_text.toLowerCase().includes(query_filter.toLowerCase())

		if (match_topic_num_filters && match_dataset_filters && match_query_filter) {
			ret.push(topic)
		}
	}

	return ret;
}
