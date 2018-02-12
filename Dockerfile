## Build Docker image for measurement and reporting of the dhcp pipelines 
## within a Docker container
##
## How to build the image:
## - Make an image for the structural pipline (see project README) 
## - Change to top-level directory of structural-pipeline-measures source tree
## - Run "docker build -t <user>/structural-pipeline-measure:latest ."
##
## Upload image to Docker Hub:
## - Log in with "docker login" if necessary
## - Push image using "docker push <user>/structural-pipeline:latest"
##

ARG USER=john
FROM ${USER}/structural-pipeline
MAINTAINER John Cupitt <jcupitt@gmail.com>
LABEL Description="dHCP structural-pipeline measure and report" Vendor="BioMedIA"

# Git repository and commit SHA from which this Docker image was built
# (see https://microbadger.com/#/labels)
ARG VCS_REF
LABEL org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/amakropoulos/structural-pipeline-measures"

RUN apt-get install -y \
	python-pip 
RUN pip install --upgrade pip

COPY . /usr/src/structural-pipeline-measure

RUN cd /usr/src/structural-pipeline-measure \
    && pip install packages/structural_dhcp_svg2rlg-0.3/ \
    && pip install packages/structural_dhcp_rst2pdf-aquavitae/ \
    && pip install packages/structural_dhcp_mriqc/ 

