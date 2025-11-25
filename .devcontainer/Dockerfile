# docker build -t webis/ir-lab-wise-2025:0.0.1 -f .devcontainer/Dockerfile .
FROM webis/ir-lab-wise-2023:0.0.3

RUN pip3 uninstall -y python-terrier tira \
	&& pip3 install 'pyterrier>=1.0.0' 'tira>=0.0.189' \
	&& python3 -c 'from tira.third_party_integrations import ensure_pyterrier_is_loaded; ensure_pyterrier_is_loaded(is_offline=False)'
