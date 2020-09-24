from ubuntu:20.04

LABEL maintainer="jannetta.steyn@newcastle.ac.uk"

ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

## Make directory for jupyter configuration file
RUN mkdir /root/.jupyter
COPY jupyter_notebook_config.py /root/.jupyter/.

## Download and install required Linux packages
RUN apt-get -qq update && apt-get -qq -y install curl wget bzip2 git gcc vim unixodbc-dev python3-dev g++ postgresql-client r-base r-base-core r-base-dev \
	&& wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
	&& bash Miniconda3-latest-Linux-x86_64.sh -bfp /usr/local/conda \
	&& conda install -y python=3 \
	&& conda update conda \
	&& apt-get -qq -y remove curl bzip2 \
	&& apt-get -qq -y autoremove \
	&& apt-get autoclean \
	&& rm -rf /var/lib/apt/lists/* /var/log/dpkg.log \
	&& conda clean --all --yes

## monitor directory
RUN cd /
RUN mkdir /monitor 
RUN mkdir /monitor/examples 
RUN mkdir /monitor/modmon 
RUN mkdir /monitor/notebooks
COPY requirements.txt /monitor/
COPY README.md /monitor/
COPY setup.py /monitor/
COPY examples/ /monitor/examples/
COPY modmon/ /monitor/modmon/
COPY defaults.ini /root/.modmon.ini
COPY notebooks/ /monitor/notebooks
RUN cd /monitor ; ls -lah 
RUN cd /monitor ; pip3 install -r dockerrequirements.txt
RUN cd /monitor ; pip3 install .

## modmon directory
RUN cd /
RUN mkdir /modmon
RUN mkdir /modmon/reports
RUN conda create -n ModMon -y python=3.8
RUN exec bash && conda init bash && exit && exec bash && conda activate ModMon && cd /monitor 

WORKDIR /modmon/
ENV PATH /opt/conda/bin:$PATH
ENV CONDA_EXE /usr/local/conda/bin/conda

VOLUME juptyerlab
EXPOSE 8888
SHELL ["/usr/bin/bash", "-c", "jupyter lab --port=8888 --no-browser --ip=0.0.0.0 --allow-root"]
ENTRYPOINT jupyter lab --port=8888 --no-browser --ip=0.0.0.0 --allow-root
# CMD tail -f /dev/null
