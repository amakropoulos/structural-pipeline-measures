#!/bin/bash
f=$1
hull=$2
outpre=$3
super=""
if [ $# -gt 3 ];then super=$4; fi


if [ -n "$DRAWEMDIR" ]; then
  [ -d "$DRAWEMDIR" ] || { echo "DRAWEMDIR environment variable invalid!" 1>&2; exit 1; }
else
  echo "DRAWEMDIR environment variable not set!" 1>&2; exit 1;
fi


A=`mirtk info $f -area | grep "surface area" |cut -d':' -f2 |tr -d ' '`
# V=`polydatavolume $hull`
V=`mirtk info $hull -area | grep volume | tr -d ' ' | cut -d':' -f2`
T=`perl -e 'use Math::Trig;print ( ( 3*$ARGV[0]/(4*pi) ) ** (1/3))' $V`

corts=`cat $DRAWEMDIR/parameters/cortical.csv`
num_orig_corts=`echo $corts| wc -w`
if [ "$super" != "" ];then 
  supstructures=`cat $super|cut -d' ' -f1|sort |uniq`
  # $s-2 means second column of super structure $s
  for s in ${supstructures};do corts="$corts $s-2 $s-3";done
fi





r=0
for l in 0 ${corts};do

  mask="-mask drawem $l"
  if [ $l == 0 ];then mask="-maskgt drawem 0";fi
  if [ $r -gt $num_orig_corts ];then
    lstr=`echo $l |cut -d'-' -f1`; lh=`echo $l |cut -d'-' -f2`
    substructures=`cat $super | grep "^$lstr " |cut -d' ' -f$lh`
    mask="-mask drawem $substructures"
  fi

  #thickness
  Th=`surface-scalar-statistics $f $mask -name thickness      |grep "^Median  "|tr -d ' ' |cut -d':' -f 2 | sed -e 's/[eE]+*/\\*10\\^/'`
  Thl[$r]=$Th

  #sulcation
  Su=`surface-scalar-statistics $f $mask -name sulc    |grep "^Median  "|tr -d ' ' |cut -d':' -f 2 | sed -e 's/[eE]+*/\\*10\\^/'`
  Sul[$r]=`echo "scale=5;$Su*$T"|bc`

  #surface area
  Sa=`surface-scalar-statistics $f $mask -name sulc    |grep "^Area  "  |tr -d ' ' |cut -d':' -f 2 | sed -e 's/[eE]+*/\\*10\\^/'`
  Sal[$r]=$Sa
  Sarl[$r]=`echo "scale=5;$Sa/$A"|bc`

  #curvature
  Mc=`surface-scalar-statistics $f $mask -name curvature  |grep "^Median  "|tr -d ' ' |cut -d':' -f 2 | sed -e 's/[eE]+*/\\*10\\^/'`
  Mcl[$r]=`echo "scale=5;$Mc*$T"|bc`

  let r=r+1
done


echo ${Thl[0]} > $outpre-thickness
echo ${Thl[*]} | cut -d' ' -f2- > $outpre-thickness-regions

echo ${Sul[0]} > $outpre-sulc
echo ${Sul[*]} | cut -d' ' -f2- > $outpre-sulc-regions

echo ${Sal[0]} > $outpre-surface-area
echo ${Sal[*]} | cut -d' ' -f2- > $outpre-surface-area-regions
echo ${Sarl[*]} | cut -d' ' -f2- > $outpre-rel-surface-area-regions

echo ${Mcl[0]} > $outpre-curvature
echo ${Mcl[*]} | cut -d' ' -f2- > $outpre-curvature-regions
