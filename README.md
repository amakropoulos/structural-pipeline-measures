# Measurements/Reporting for the dHCP Structural Pipeline

This is an additional package that computes measurements and creates reports for the dHCP Structural Pipeline.

The measurements include:<br>
* volumes
* cortical surface measurements (surface area, thickness, curvature, sulcal depth, gyrification index (GI) )

## Developers
<b>Antonios Makropoulos</b>:  <a href="http://antoniosmakropoulos.com">more</a>

## License
The measurements/reporting dHCP structural pipeline are distributed under the terms outlined in LICENSE.txt

## Install and run with docker
You can build the tool in a docker container. This will work on any
version of any platform, is automated, and fairly simple. First, install
docker:

https://docs.docker.com/engine/installation/

Then in the top directory of `structural-pipeline-measure`, use git to 
switch to the branch you want to build, and enter:

```
# docker build --build-arg USER=<user> -t <user>/structural-pipeline-measures:latest .
```

Substituting `<user>` for your username. This command must be run as root. 

This will create a single docker image called
`<user>/structural-pipeline-measures:latest` containing all the required files 
and all required dependencies. 

You can then execute the tool like this (for example):

```
# docker run --rm -t -v $PWD/data:/data \
    -u $(id -u <user>):$(id -g <user>) \
    <user>/structural-pipeline-measures:latest \
    bash -c ". /usr/src/structural-pipeline/parameters/path.sh; \
        cd /usr/src/structural-pipeline-measures; \
        ./pipeline.sh /data/derivatives /data/dataset_csv -d /data --reporting"
```

Again, this must be run as root. This will mount the subdirectory `data` of
your current directory as `/data` in the container, then execute the tool
on the output of `structural-pipeline` in that directory. 

## Install locally
If you want to work on the code of the pipeline, it can be more convenient to
install locally to your machine. Only read on if you need to do a local
install. 

## Installation
The measurements scripts do not require installation.

The reporting (optional) can be installed as follows:
* pip install packages/structural_dhcp_svg2rlg-0.3/
* pip install packages/structural_dhcp_rst2pdf-aquavitae/
* pip install packages/structural_dhcp_mriqc/


## Run
In order to run this pipeline, the dHCP structural pipeline commands/tools need to be included in the shell PATH by running:
* . [dHCP_structural_pipeline_path]/parameters/path.sh
<br>

The pipeline can be run with the following command:

* ./pipeline.sh [derivatives_dir] [dataset_csv]  \( --reporting \) \( -t [num_threads] \)

where:

| Argument        | Type      | Description     
| ------------- |:-------------:| :-------------:|
| derivatives_dir| string | The derivatives directory created from the structural pipeline
| dataset_csv| CSV file | This is a comma-delimited file (CSV) with the sessions to be included in the measurements/reporting. <br>It includes one line for each subject session: [subjectID], [sessionID], [age] e.g. <br>subject-1, session-1, 32<br>subject-1, session-2, 44<br>...<br>subject-N, session-1, 36<br>
| num_threads| integer |Number of threads (CPU cores) used (default: 1) (Optional)
If specified (--reporting), the pipeline will also generate PDF reports for the subjects.


Examples:
* ./pipeline.sh derivatives dataset.csv
* ./pipeline.sh derivatives dataset.csv --reporting
* ./pipeline.sh derivatives dataset.csv --reporting -t 8


The output of the pipeline is the following files:

| Output    | Description    
| -------------  |:-------------:|
| [derivatives_dir]/anat_group_measurements.csv   | CSV file that contains all the measurements for the sessions included
| [derivatives_dir]/anat_group.pdf    | PDF that specifies the sessions included (if --reporting is specified)
| [derivatives_dir]/anat_group_qc.pdf  | PDF report for all the sessions (if --reporting is specified)
| [derivatives_dir]/sub-\*/ses-\*/anat/sub-\*_ses-\*_qc.pdf  | PDF report for each session (if --reporting is specified)


