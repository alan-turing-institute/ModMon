from ubuntu:20.04

LABEL maintainer="jannetta.steyn@newcastle.ac.uk"

ENV TZ=Europe/London
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

## Make directory for jupyter configuration file
RUN mkdir /root/.jupyter
COPY jupyter_notebook_config.py /root/.jupyter/.
ENV PATH $PATH:/usr/local/conda/bin

## Download and install required Linux packages
RUN apt-get -qq update && apt-get -qq -y install gnupg curl wget bzip2 git gcc vim unixodbc-dev python3-dev g++ postgresql-client r-base r-base-core r-base-dev \
	&& wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
	&& bash Miniconda3-latest-Linux-x86_64.sh -bfp /usr/local/conda \
	&& conda install -y python=3 \
	&& conda update conda \
	&& apt-get -qq -y autoremove \
	&& apt-get autoclean \
	&& rm -rf /var/lib/apt/lists/* /var/log/dpkg.log \
	&& conda clean --all --yes
	# && apt-get -qq -y remove curl bzip2 \

## monitor directory
RUN cd /
RUN mkdir /monitor 
RUN mkdir /monitor/examples 
RUN mkdir /monitor/modmon 
RUN mkdir /monitor/notebooks
COPY requirements.txt /monitor/
COPY dockerrequirements.txt /monitor/
COPY README.md /monitor/
COPY setup.py /monitor/
COPY examples/ /monitor/examples/
COPY modmon/ /monitor/modmon/
COPY defaults.ini /root/.modmon.ini
COPY notebooks/ /monitor/notebooks
RUN cd /monitor ; ls -lah 
RUN cd /monitor ; pip3 install -r dockerrequirements.txt
RUN cd /monitor ; pip3 install .

## install sql driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update -y
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17
RUN ACCEPT_EULA=Y apt-get install -y mssql-tools
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
# optional: for unixODBC development headers
RUN apt-get install unixodbc-dev

## modmon directory
RUN cd /
RUN mkdir /modmon
RUN mkdir /modmon/reports
RUN conda create -n ModMon -y python=3.8
RUN exec bash && conda init bash && exit && exec bash && conda activate ModMon && cd /monitor 

## install jre
RUN apt-get install -y openjdk-14-jre-headless
## install ModelServer
COPY ModelServer.jar /root/
RUN java -cp /root/ModelServer.jar uk.ac.ncl.ModelServer.MainApplication &

ENV PATH /opt/conda/bin:$PATH
ENV CONDA_EXE /usr/local/conda/bin/conda
WORKDIR /modmon/
# external volume for data
VOLUME juptyerlab
# expose jupyterlab on port
EXPOSE 8888
EXPOSE 4567
SHELL ["/usr/bin/bash", "-c", "jupyter lab --port=8888 --no-browser --ip=0.0.0.0 --allow-root"]
# run jupyterlab
ENTRYPOINT jupyter lab --port=8888 --no-browser --ip=0.0.0.0 --allow-root
# CMD tail -f /dev/null
