import {extractFromUrl, updateUrl, get} from '../utils'
import 'cross-fetch/polyfill';

Object.defineProperty((window as Window), 'location', {
  value: {
    href: ''
  },
  writable: true // possibility to override
});

test('Method extractFromUrl can be imported and is defined.', () => {
    expect(extractFromUrl).toBeDefined()
})

test('Default value is returned when parameter is not found.', () => {
    expect(extractFromUrl('not_found', 'default')).toEqual('default')
})

test('Parameter is extracted when first parameter.', () => {
    (window as Window).location.href = "?hello=foo&sd"

    expect(extractFromUrl('hello')).toEqual('foo')
})

test('Parameter is extracted when from last parameter', () => {
    (window as Window).location.href = "?hello=foo&sd=1"

    expect(extractFromUrl('sd')).toEqual('1')
})

test('Method updateUrl can be imported and is defined.', () => {
    expect(updateUrl).toBeDefined()
})

test('updateUrl changes removes unused parameters.', () => {
    (window as Window).location.href = "my-url?will-be-removed=dsa"

    expect(updateUrl()).toEqual('my-url')
})

test('updateUrl changes the topic and removes unused parameters.', () => {
    (window as Window).location.href = "my-url?will-be-removed=dsa&topic=foo"

    expect(updateUrl('hello')).toEqual('my-url?topic=hello')
})

test('updateUrl changes the dataset and removes unused parameters.', () => {
    (window as Window).location.href = "my-url?will-be-removed=dsa&topic=foo&dataset=foo"

    expect(updateUrl(null, 'ds')).toEqual('my-url?dataset=ds')
})

test('updateUrl changes the dataset and removes unused parameters.', () => {
    (window as Window).location.href = "my-url?will-be-removed=dsa&topic=foo&dataset=foo&query=qs"

    expect(updateUrl(null, null, 'q')).toEqual('my-url?query=q')
})


test('Method get can be imported and is defined.', () => {
    expect(get).toBeDefined()
})

test('Method get returns object from cache.', async () => {
    const obj = Object()
    obj.$data = {'cache': {'path-does-not-exist': {'1-2': 'foo'}}}
    const request = {'path': 'path-does-not-exist', 'start': '1', 'end': '2'}
    const response = await get(request, obj)

    expect(response).toBe("foo")
})

test('Method get returns object from cache if multiple_keys_exist.', async () => {
    const obj = Object()
    obj.$data = {'cache': {'path-does-not-exist': {'1-2': 'foo', '1-4': 'foobar'}}}
    const request = {'path': 'path-does-not-exist', 'start': 1, 'end': 4}
    const response = await get(request, obj)

    expect(response).toBe("foobar")
})

test('Method get returns against real http resource', async () => {
    const obj = Object()

    obj.$data = {'cache': {'https://mam10eks.github.io/github-page-tutorial/run-details.jsonl': {}}}
    const request = {'path': 'https://mam10eks.github.io/github-page-tutorial/run-details.jsonl', 'start': 108008, 'end': 109203}
    const response = await get(request, obj)

    expect(response["dataset"]).toBe("vaswani")
    expect(response["qid"]).toBe("93")
    expect(response["default_text"]).toBe("HIGH FREQUENCY OSCILLATORS USING TRANSISTORS THEORETICAL TREATMENT AND PRACTICAL CIRCUIT DETAILS\n")
})

test('Error is thrown for wrong endpoints.', async () => {
    const obj = Object()

    obj.$data = {'cache': {'https://mam10eks.github.io/github-page-tutorial/': {}}}
    const request = {'path': 'https://mam10eks.github.io/github-page-tutorial/', 'start': 1000, 'end': 1002}

    try {
        await get(request, obj)
    } catch (e) { 
        return
    }

    fail("No error was thrown.")
})

