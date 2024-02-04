build-ui-docker:
	docker run --rm -v ${PWD}:/app -v ${PWD}/static/dist/:/dist -w /app --entrypoint ./process_data.py mam10eks/github-page-tutorial:0.0.2
	docker run --rm -v ${PWD}:/app -v ${PWD}/static/dist/:/dist -w /app --entrypoint vite mam10eks/github-page-tutorial:0.0.2 build

coverage:
	 pytest --cov=construct_indices \
	 && coverage-badge -o construct_indices/coverage.svg
