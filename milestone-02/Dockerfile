# We start from a docker image that already has all dependencies installed
FROM webis/tira-ir-starter-pyterrier:0.0.2-base

# We remove some non-required files from our starting image
RUN rm /workspace/*.ipynb /workspace/default_pipelines.py /workspace/pyterrier_cli.py

COPY *.ipynb /workspace/

RUN jupyter trust /workspace/*.ipynb

# For local development, we start a jupyter notebook by default
ENTRYPOINT ["jupyter", "notebook", "--allow-root", "--ip", "0.0.0.0"]

