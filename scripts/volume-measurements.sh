#!/bin/bash
subj=$1
anatDir=$2
outpre=$3
super=""
if [ $# -gt 3 ];then super=$4; fi



super_vol=""
super_all_vol=""
if [ "$super" != "" ];then 
  supstructures=`cat $super|cut -d' ' -f1|sort |uniq`
  for s in ${supstructures};do
    for col in {2..5};do
      substructures=`cat $super | grep "^$s "|cut -d' ' -f $col`
      multipadding $anatDir/${subj}_drawem_all_labels.nii.gz $anatDir/${subj}_drawem_all_labels.nii.gz $outpre-temp.nii.gz `echo $substructures | wc -w` $substructures 0 -invert
      vol[$col]=`fslstats $outpre-temp.nii.gz -V|cut -d' ' -f2`
    done
    vol[0]=`echo "scale=3; ${vol[2]}+${vol[4]}" | /usr/bin/bc`
    vol[1]=`echo "scale=3; ${vol[3]}+${vol[5]}" | /usr/bin/bc`
    super_vol="$super_vol ${vol[0]} ${vol[1]}"
    super_all_vol="$super_all_vol ${vol[2]} ${vol[3]} ${vol[4]} ${vol[5]}"
  done
fi

mirtk padding $anatDir/${subj}_drawem_all_labels.nii.gz $anatDir/${subj}_drawem_all_labels.nii.gz $outpre-temp.nii.gz 4 49 50 83 84 0
vol=`fslstats $outpre-temp.nii.gz -V|cut -d' ' -f2`
echo $vol > $outpre-volume
rm $outpre-temp.nii.gz

line=`mirtk measure-volume $anatDir/${subj}_drawem_tissue_labels.nii.gz |cut -d' ' -f2`
line=`echo $line`; 
echo "$line"  > $outpre-volume-tissue-regions
rline=""; for l in ${line};do rline=$rline`echo "scale=5;$l/$vol"|bc`" ";done
echo $rline > $outpre-rel-volume-tissue-regions

line=`mirtk measure-volume $anatDir/${subj}_drawem_all_labels.nii.gz |cut -d' ' -f2` 
line=`echo $line`"$super_all_vol"
echo "$line" > $outpre-volume-all-regions
rline=""; for l in ${line};do rline=$rline`echo "scale=5;$l/$vol"|bc`" ";done
echo $rline > $outpre-rel-volume-all-regions
