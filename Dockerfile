## Build Docker image for measurement and reporting of the dhcp pipelines 
## within a Docker container
##
## How to build the image:
## - Make an image for the structural pipline (see project README) 
## - Change to top-level directory of structural-pipeline-measures source tree
## - Run "docker build -t <user>/structural-pipeline-measures:latest ."
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
	python3-pip
RUN pip3 install --upgrade pip

# these packages are listed in packages/*/requirement.txt
# install them now to speed up structural-pipeline-measure install later
#
# nipype insists on prov 1.5.0
RUN pip3 install --upgrade \
	h5py==2.6.0 \
	mock \
	numpy \
	six \
	pandas \
	nitime \
	dipy \
	lockfile \
	jinja2 \
	seaborn \
	pyPdf2 \
	PyYAML \
	future \
	simplejson \
	prov==1.5.0 \
	smartypants \
	rson \
	tenjin \
	aafigure \
	nipype \
	alabaster \
	Babel \
	coverage \
	docutils \
	MarkupSafe \
	nose \
	pdfrw \
	Pillow \
	Pygments \
	pytz \
	reportlab \
	snowballstemmer \
	Sphinx \
	sphinx-rtd-theme 

COPY . /usr/src/structural-pipeline-measures

RUN cd /usr/src/structural-pipeline-measures \
    && pip3 install packages/structural_dhcp_svg2rlg-0.3/ \
    && pip3 install packages/structural_dhcp_rst2pdf-aquavitae/ \
    && pip3 install packages/structural_dhcp_mriqc/ 

