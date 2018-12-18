#!/bin/bash

# if FSLDIR is not defined, assume we need to read the FSL startup
if [ -z ${FSLDIR+x} ]; then
  if [ ! -f /etc/fsl/fsl.sh ]; then
    echo FSLDIR is not set and there is no system-wide FSL startup
    exit 1
  fi

  . /etc/fsl/fsl.sh
fi 

usage()
{
  base=$(basename "$0")
  echo "usage: $base derivatives_dir dataset_csv [options]
This script computes the different measurements for the dHCP structural pipeline,
 and if specified creates pdf reports for the subjects (option --QC).

Arguments:
  derivatives_dir               The derivatives directory created from the structural pipeline.
                                The script additionally creates a pdf report for the subjects specified in the <csv> file.
  dataset_csv                   The dataset_csv file is a comma-delimited file with a line for each subject session:
                                   <subjectID>, <sessionID>, <age>
                                e.g.
                                   subject-1, session-1, 32
                                   subject-1, session-2, 44
                                          ...
                                   subject-N, session-1, 36

Options:
  --reporting                   The script will additionally create a pdf report for each subject, and a group report.    
  -t / -threads  <number>       Number of threads (CPU cores) used (default: 1)
  -d / -data-dir  <directory>   The directory used to run the script and output the files. 
  -h / -help / --help           Print usage.
"
  exit;
}

################ ARGUMENTS ################

[ $# -ge 2 ] || { usage; }
command=$@
derivatives_dir=$1
dataset_csv=$2

QC=0
threads=1
datadir=`pwd`
scriptdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"/scripts

shift; shift;
while [ $# -gt 0 ]; do
  case "$1" in
    --reporting)  QC=1; ;;
    -d|-data-dir)  shift; datadir=$1; ;;
    -t|-threads)  shift; threads=$1; ;;
    -h|-help|--help) usage; ;;
    -*) echo "$0: Unrecognized option $1" >&2; usage; ;;
     *) break ;;
  esac
  shift
done

echo "Reporting for the dHCP pipeline
Derivatives directory:  $derivatives_dir 
Dataset CSV:            $dataset_csv
datadir:            	$datadir
QC (reporting): 	$QC

$BASH_SOURCE $command
----------------------------"


derivatives_dir=`echo "$(cd "$(dirname "$derivatives_dir")"; pwd)/$(basename "$derivatives_dir")"`
reportsdir=$datadir/reports
workdir=$reportsdir/workdir
logdir=$datadir/logs
mkdir -p $logdir


################ MEASURES PIPELINE ################

echo "computing volume/surface measurements of subjects..."
while IFS= read -r line || [ -n "$line" ]; do
  s=`echo $line | cut -d',' -f1 | sed -e 's:sub-::g' |sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  e=`echo $line | cut -d',' -f2 | sed -e 's:ses-::g' |sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  a=`echo $line | cut -d',' -f3 | sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  echo "$s $e"
  $scriptdir/compute-measurements.sh $s $e $derivatives_dir/sub-$s/ses-$e/anat -d $workdir > $logdir/$s-$e-measures.log 2> $logdir/$s-$e-measures.err
done < $dataset_csv
echo ""



# gather measures
echo "gathering volume/surface measurements of subjects..."
measfile=$reportsdir/pipeline_all_measures.csv
rm -f $measfile

# measures
stats="volume volume-tissue-regions rel-volume-tissue-regions volume-all-regions rel-volume-all-regions thickness thickness-regions sulc sulc-regions curvature curvature-regions GI GI-regions surface-area surface-area-regions rel-surface-area-regions"
typeset -A name

# header
lbldir=$scriptdir/../label_names
header="subject ID, session ID, age at scan"
for c in ${stats}; do
  if [[ $c == *"tissue-regions"* ]];then labels=$lbldir/tissue_labels.csv 
  elif [[ $c == *"all-regions"* ]];then labels=$lbldir/all_labels.csv
  elif [[ $c == *"regions"* ]];then labels=$lbldir/cortical_labels.csv 
  else labels=""; fi
  cname=`echo $c | sed -e 's:-tissue-regions::g'| sed -e 's:-all-regions::g'| sed -e 's:-regions::g'`
  if [ "$labels" == "" ];then header="$header,$cname";
  else
    while read l;do 
      sname=`echo "$l"|cut -f2|sed -e 's:,::g'`;
      header="$header,$cname - $sname";
    done < $labels
  fi
done

# measurements
echo "$header"> $measfile
while IFS= read -r line || [ -n "$line" ]; do
  s=`echo $line | cut -d',' -f1 | sed -e 's:sub-::g' |sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  e=`echo $line | cut -d',' -f2 | sed -e 's:ses-::g' |sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  a=`echo $line | cut -d',' -f3 | sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  subj="sub-${s}_ses-$e"
  line="$s,$e,$a"
  for c in ${stats};do
    if [ -f $workdir/$subj/$subj-$c ]; then 
      line="$line,"`cat $workdir/$subj/$subj-$c |sed -e 's: :,:g' `
    fi
  done
  echo "$line" |sed -e 's: :,:g' >> $measfile
done < $dataset_csv


echo "completed volume/surface measurements"


################ REPORTS PIPELINE ################

if  [ $QC -eq 0 ];then exit;fi

echo "----------------------------
"

echo "computing QC measurements for subjects..."

subjs=""
while IFS= read -r line || [ -n "$line" ]; do
  s=`echo $line | cut -d',' -f1 | sed -e 's:sub-::g' |sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  e=`echo $line | cut -d',' -f2 | sed -e 's:ses-::g' |sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  a=`echo $line | cut -d',' -f3 | sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  subj="sub-${s}_ses-$e"
  echo "$s $e"
  $scriptdir/compute-QC-measurements.sh $s $e $a $derivatives_dir/sub-$s/ses-$e/anat -d $workdir >> $logdir/$s-$e-measures.log 2>> $logdir/$s-$e-measures.err
  subjs="$subjs $subj"
done < $dataset_csv
echo ""

# gather measures
echo "gathering QC measurements of subjects..."

for json in dhcp-measurements.json qc-measurements.json;do
  echo "{\"data\":[" > $reportsdir/$json
  first=1
  for subj in ${subjs};do
    files=`ls $workdir/$subj/*$json`
    for f in ${files};do 
      line=`cat $f`
      if [ $first -eq 1 ];then first=0; else line=",$line";fi
      echo $line >> $reportsdir/$json
    done
  done
  echo "]}" >> $reportsdir/$json
done

# create reports
echo "creating QC reports..."
structural_dhcp_mriqc -o $reportsdir -w $workdir --dhcp-measures $reportsdir/dhcp-measurements.json --qc-measures $reportsdir/qc-measurements.json --nthreads $threads >> $logdir/$s-$e-measures.log 2>> $logdir/$s-$e-measures.err


echo "copying reports..."
while IFS= read -r line || [ -n "$line" ]; do
  s=`echo $line | cut -d',' -f1 | sed -e 's:sub-::g' |sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  e=`echo $line | cut -d',' -f2 | sed -e 's:ses-::g' |sed 's/[[:blank:]]*$//' | sed 's/^[[:blank:]]*//' `
  cp $reportsdir/anatomical_${s}.pdf $derivatives_dir/sub-$s/ses-$e/anat/sub-${s}_ses-${e}_qc.pdf
done < $dataset_csv

cp $reportsdir/anatomical_group.pdf $derivatives_dir/anat_group.pdf
cp $reportsdir/anatomical_group_stats.pdf $derivatives_dir/anat_group_qc.pdf
cp $reportsdir/pipeline_all_measures.csv $derivatives_dir/anat_group_measurements.csv
echo "completed QC reports"
