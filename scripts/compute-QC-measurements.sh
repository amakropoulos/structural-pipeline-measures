 #!/bin/bash

usage()
{
  base=$(basename "$0")
  echo "usage: $base subjectID sessionID scan_age derivatives_anat_dir [options]
This script computes the different measurements for the dHCP structural pipeline QC.

Arguments:
  subjectID                     subject ID
  sessionID                     session ID
  scan_age                      Number: Subject age in weeks. 
  derivatives_anat_dir          The anat dir inside the processed derivatives directory of the structural pipeline

Options:
  -d / -data-dir  <directory>   The directory used to run the script and output the files. 
  -h / -help / --help           Print usage.
"
  exit;
}

run(){
  echo "$@" 
  "$@" 
  if [ ! $? -eq 0 ]; then
    echo " failed: see log file logs/$subj-err for details"
    exit 1
  fi
}
################ ARGUMENTS ################

[ $# -ge 2 ] || { usage; }
command=$@
subjectID=$1
sessionID=$2
age=$3
anatDir=$4

datadir=`pwd`
scriptdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

shift; shift; shift; shift;
while [ $# -gt 0 ]; do
  case "$1" in
    -d|-data-dir)  shift; datadir=$1; ;;
    -h|-help|--help) usage; ;;
    -*) echo "$0: Unrecognized option $1" >&2; usage; ;;
     *) break ;;
  esac
  shift
done

mkdir -p $datadir
cd $datadir

subj=sub-${subjectID}_ses-${sessionID}
outdir=$subj
mkdir -p $outdir/temp logs


rage=`printf "%.*f\n" 0 $age`
if [ -f $anatDir/${subj}_T2w.nii.gz ];then T2ex="True"; else T2ex="False"; fi
if [ -f $anatDir/${subj}_T1w.nii.gz  ];then T1ex="True"; else T1ex="False"; fi

if [ ! -f $outdir/dhcp-measurements.json ];then 

    # prepare files
    if [ -f $anatDir/${subj}_T2w.nii.gz -o -f $anatDir/${subj}_T1w.nii.gz ];then
      run mirtk padding $anatDir/${subj}_drawem_tissue_labels.nii.gz $anatDir/${subj}_drawem_tissue_labels.nii.gz $outdir/temp/tissue_labels.nii.gz 1 0 -1 1 4 0
      #masks
      thr=0
      for t in "bg" csf gm wm;do 
        if [ "$t" == "bg" ];then 
          run fslmaths $outdir/temp/tissue_labels.nii.gz -add 1 -thr 1 -uthr 1 -bin $outdir/temp/${t}_mask.nii.gz
        else
          run fslmaths $outdir/temp/tissue_labels.nii.gz -thr $thr -uthr $thr -bin $outdir/temp/${t}_mask.nii.gz
        fi
        run mirtk erode-image $outdir/temp/${t}_mask.nii.gz $outdir/temp/${t}_mask_open.nii.gz -connectivity 18 > /dev/null 2>&1 
        run mirtk dilate-image $outdir/temp/${t}_mask_open.nii.gz $outdir/temp/${t}_mask_open.nii.gz -connectivity 18 > /dev/null 2>&1 
        let thr=$thr+1
      done
    fi

    # T2 QC measures
    if [ -f $anatDir/${subj}_T2w.nii.gz ];then
      if [ ! -f $outdir/T2-qc-measurements.json ];then 
        cp $anatDir/${subj}_T2w_biasfield.nii.gz $outdir/temp/T2_bias.nii.gz
        run mirtk convert-image $anatDir/${subj}_T2w_restore.nii.gz $outdir/temp/T2.nii.gz -rescale 0 1000
        run fslmaths $outdir/temp/T2.nii.gz -mul $anatDir/${subj}_brainmask_bet.nii.gz $outdir/temp/T2_restore_brain.nii.gz
        $scriptdir/image-QC-measurements.sh $outdir/temp T2 $subjectID $sessionID $anatDir/${subj}_T2w.nii.gz $outdir/T2-qc-measurements.json
      fi
    else
      echo "{\"subject_id\":\"$subjectID\", \"session_id\":\"$sessionID\", \"run_id\":\"T2\", \"exists\":\"$T2ex\", \"reorient\":\"\" }" > $outdir/T2-qc-measurements.json
      if [ "$T2ex" == "True" ];then echo "Could not find $anatDir/${subj}_T2w.nii.gz!!!";fi
    fi

    # T1 QC measures
    if [ -f $anatDir/${subj}_T1w.nii.gz ];then
      if [ ! -f $outdir/T1-qc-measurements.json ];then 
        cp $anatDir/${subj}_T1w_biasfield.nii.gz $outdir/temp/T1_bias.nii.gz
        run mirtk convert-image $anatDir/${subj}_T1w_restore.nii.gz $outdir/temp/T1.nii.gz -rescale 0 1000
        run fslmaths $outdir/temp/T1.nii.gz -mul $anatDir/${subj}_brainmask_bet.nii.gz $outdir/temp/T1_restore_brain.nii.gz
        $scriptdir/image-QC-measurements.sh $outdir/temp T1 $subjectID $sessionID $anatDir/${subj}_T1w.nii.gz $outdir/T1-qc-measurements.json
      fi
    else
      echo "{\"subject_id\":\"$subjectID\", \"session_id\":\"$sessionID\", \"run_id\":\"T1\", \"exists\":\"$T1ex\", \"reorient\":\"\" }" > $outdir/T1-qc-measurements.json
      if [ "$T1ex" == "True" ];then echo "Could not find $anatDir/${subj}_T1w.nii.gz!!!";fi
    fi


    # pipeline QC measures
    inputOK="False"
    segOK="False"
    LhemiOK="False"
    RhemiOK="False"
    QCOK='True'
    volume_brain=''
    volume_csf=''
    volume_gm=''
    volume_wm=''
    surface_area=''
    gyrification_index=''
    thickness=''

    if [ -f $anatDir/${subj}_T2w.nii.gz ];then 
      inputOK="True"
      if [ -f $anatDir/${subj}_drawem_all_labels.nii.gz ];then segOK="True";fi
      if [ -f $anatDir/Native/${subj}_left_sphere.surf.gii ];then LhemiOK="True"; else QCOK='False';fi
      if [ -f $anatDir/Native/${subj}_right_sphere.surf.gii ];then RhemiOK="True"; else QCOK='False';fi

      # additional measures
      volume_brain=`cat $outdir//$subj-volume 2>/dev/null`
      volume_csf=`cat $outdir/$subj-volume-tissue-regions 2>/dev/null |cut -d' ' -f1`
      volume_gm=`cat $outdir/$subj-volume-tissue-regions 2>/dev/null |cut -d' ' -f2`
      volume_wm=`cat $outdir/$subj-volume-tissue-regions 2>/dev/null |cut -d' ' -f3`
      surface_area=`cat $outdir/$subj-surface-area 2>/dev/null`
      gyrification_index=`cat $outdir/$subj-GI 2>/dev/null`
      thickness=`cat $outdir/$subj-thickness 2>/dev/null`
    fi

    agemod=$((rage%2))
    let agegroup=$rage-$agemod
    let nagegroup=$agegroup+2
    if [ $nagegroup -le 28 ];then group="age<$agegroup"
    elif [ $agegroup -ge 44 ];then group="age>=$agegroup"
    else group="$agegroup<=age<$nagegroup"
    fi

    line="{\"subject_id\":\"$subjectID\", \"session_id\":\"$sessionID\", \"run_id\":\"pipeline, $group\", \"age\":\"$age\""
    line="$line, \"inputOK\":\"$inputOK\", \"segOK\":\"$segOK\", \"LhemiOK\":\"$LhemiOK\", \"RhemiOK\":\"$RhemiOK\" "
    for m in volume_brain volume_csf volume_gm volume_wm surface_area gyrification_index thickness;do
      eval "val=\$$m"
      if [ "$val" == "" ];then QCOK='False'; continue;fi
      line="$line, \"$m\":\"$val\""
    done
    line="$line, \"QCOK\":\"$QCOK\" }"
    echo $line > $outdir/dhcp-measurements.json
fi

rm -r $outdir/temp