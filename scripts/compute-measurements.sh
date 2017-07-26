#!/bin/bash

usage()
{
  base=$(basename "$0")
  echo "usage: $base subjectID sessionID derivatives_anat_dir [options]
This script computes the different measurements for the dHCP structural pipeline.

Arguments:
  subjectID                     subject ID
  sessionID                     session ID
  derivatives_anat_dir          The anat dir of the subject (inside the processed derivatives directory of the structural pipeline)

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
    echo " failed: see log file $err for details"
    exit 1
  fi
}



################ ARGUMENTS ################

[ $# -ge 1 ] || { usage; }
command=$@
subjID=$1
sessionID=$2
anatDir=$3

datadir=`pwd`

shift; shift; shift;
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

subj=sub-${subjID}_ses-${sessionID}
surfdir=$anatDir/Native
rdir=surfaces

mkdir -p $rdir $subj

scriptdir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"



# do the volume-based measurements
super_structures=$scriptdir/../label_names/super-structures.csv

if [ ! -f $subj/$subj-rel-volume-all-regions ];then 
  run $scriptdir/volume-measurements.sh $subj $anatDir $subj/$subj $super_structures
fi

if [ ! -f $subj/$subj-curvature-regions ];then 
  if [ ! -f $surfdir/${subj}_left_white.surf.gii ];then echo "The left WM surface for subject $subj doesn't exist"; exit;fi
  if [ ! -f $surfdir/${subj}_right_white.surf.gii ];then echo "The right WM surface for subject $subj doesn't exist"; exit;fi

  # gather all measurements into a single file
  if [ ! -f $rdir/${subj}_white.surf.vtk ];then
    for h in left right;do
      if [ ! -f $rdir/${subj}_${h}_white.surf.vtk ];then
        # copy surface
        tmpsurf=$rdir/${subj}_${h}_white.surf-temp.vtk
        run mirtk convert-pointset $surfdir/${subj}_${h}_white.surf.gii $tmpsurf

        # copy metrics
        for m in curvature thickness sulc drawem;do
          if [ "$m" == "drawem" ];then mtype=label;else mtype=shape;fi
          run mirtk copy-pointset-attributes $surfdir/${subj}_${h}_${m}.$mtype.gii $tmpsurf $tmpsurf -pointdata 0 $m
        done

        run mv $tmpsurf $rdir/${subj}_${h}_white.surf.vtk
      fi
    done

    run mirtk convert-pointset $rdir/${subj}_left_white.surf.vtk $rdir/${subj}_right_white.surf.vtk $rdir/${subj}_white.surf.vtk
    rm $rdir/${subj}_left_white.surf.vtk $rdir/${subj}_right_white.surf.vtk
  fi

  # project labels to pial
  if [ ! -f $rdir/${subj}_pial.surf.vtk ];then
    for h in left right;do
      run mirtk copy-pointset-attributes $surfdir/${subj}_${h}_drawem.label.gii $surfdir/${subj}_${h}_pial.surf.gii $rdir/${subj}_${h}_pial.surf.vtk -pointdata 0 drawem
    done
    run mirtk convert-pointset $rdir/${subj}_left_pial.surf.vtk $rdir/${subj}_right_pial.surf.vtk $rdir/${subj}_pial.surf.vtk
  fi


  # compute the convex hull
  if [ ! -f $rdir/${subj}_outerpial.surf.vtk ];then 
    for h in left right;do
      if [ ! -f $rdir/${subj}_${h}_outerpial.surf.vtk ];then
        if [ "$h" == "left" ];then
          run fslmaths $anatDir/${subj}_ribbon.nii.gz -thr 2 -uthr 3 -bin $rdir/${subj}_${h}_outerpial.nii.gz
        else
          run fslmaths $anatDir/${subj}_ribbon.nii.gz -thr 41 -uthr 42 -bin $rdir/${subj}_${h}_outerpial.nii.gz
        fi
        # compute outside surface for GI
        run mirtk dilate-image $rdir/${subj}_${h}_outerpial.nii.gz $rdir/${subj}_${h}_outerpial.nii.gz -iterations 3
        run mirtk erode-image $rdir/${subj}_${h}_outerpial.nii.gz $rdir/${subj}_${h}_outerpial.nii.gz -iterations 2
        run mirtk extract-surface $rdir/${subj}_${h}_outerpial.nii.gz $rdir/${subj}_${h}_outerpial.surf-temp.vtk -isovalue 0.5 -blur 1 
        # project labels
        run mirtk project-onto-surface $rdir/${subj}_${h}_outerpial.surf-temp.vtk $rdir/${subj}_${h}_outerpial.surf.vtk -surface $rdir/${subj}_${h}_pial.surf.vtk -scalars drawem
        run rm $rdir/${subj}_${h}_outerpial.nii.gz $rdir/${subj}_${h}_outerpial.surf-temp.vtk
      fi
    done  
    run mirtk convert-pointset $rdir/${subj}_left_outerpial.surf.vtk $rdir/${subj}_right_outerpial.surf.vtk $rdir/${subj}_outerpial.surf.vtk
    run rm $rdir/${subj}_left_outerpial.surf.vtk $rdir/${subj}_right_outerpial.surf.vtk $rdir/${subj}_left_pial.surf.vtk $rdir/${subj}_right_pial.surf.vtk
  fi

  # measure GI
  run $scriptdir/GI-measurements.sh $rdir/${subj}_pial.surf.vtk $rdir/${subj}_outerpial.surf.vtk $subj/$subj $super_structures

  # do the surface-based measurements (convex-hull norm)
  run $scriptdir/surface-measurements.sh $rdir/${subj}_white.surf.vtk $rdir/${subj}_outerpial.surf.vtk $subj/$subj $super_structures

  #clean-up
  rm $rdir/${subj}_*
fi
