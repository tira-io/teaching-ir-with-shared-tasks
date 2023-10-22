FROM ubuntu:22.04

# Install dependencies
RUN apt-get update \
	&& apt-get upgrade -y \
	&& apt-get install -y jq libffi-dev python3 python3-pip python-is-python3 openjdk-11-jdk wget \
	&& pip3 install jupyter ir_datasets \
	&& rm -Rf /var/cache/apt \
	&& rm -Rf /root/.cache/pip \
	&& pip3 install tira python-terrier chatnoir-api \
	&& python3 -c 'import pyterrier as pt; pt.init(boot_packages=["com.github.terrierteam:terrier-prf:-SNAPSHOT"])' \
	&& wget https://files.webis.de/software/pyterrier-plugins/custom-terrier-token-processing-1.0-SNAPSHOT-jar-with-dependencies.jar -O /root/.pyterrier/custom-terrier-token-processing-0.0.1.jar
