FROM ubuntu:26.04

# Install system dependencies
RUN apt-get update \
	&& apt-get upgrade -y \
	&& apt-get install -y jq libffi-dev python3 python3-pip python-is-python3 openjdk-11-jdk wget

# Install Python dependencies
RUN pip3 install 'chatnoir-api~=3.4' 'ir_datasets~=0.5.11' jupyter 'pyterrier[java]~=1.0' 'tira~=0.0.207' 'trectools~=0.0.50'

# Install custom Terrier token processing plugin
RUN mkdir -p /root/.pyterrier \
    && wget https://files.webis.de/software/pyterrier-plugins/custom-terrier-token-processing-1.0-SNAPSHOT-jar-with-dependencies.jar -O /root/.pyterrier/custom-terrier-token-processing-0.0.1.jar

# Clean up caches
RUN rm -Rf /var/cache/apt \
	&& rm -Rf /root/.cache/pip

# Ensure that PyTerrier is loaded and the custom plugin is registered
RUN python3 -c 'from tira.third_party_integrations import ensure_pyterrier_is_loaded; ensure_pyterrier_is_loaded(is_offline=False)'
