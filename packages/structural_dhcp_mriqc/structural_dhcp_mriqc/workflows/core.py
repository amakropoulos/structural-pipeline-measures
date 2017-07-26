#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# @Author: oesteban
# @Date:   2016-01-05 11:24:05
# @Email:  code@oscaresteban.es
# @Last modified by:   oesteban
# @Last Modified time: 2016-05-04 14:53:43
""" The core module combines the existing workflows """
from six import string_types
from .anatomical import anat_qc_workflow
from .functional import fmri_qc_workflow
from ..utils.misc import gather_bids_data

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu



# def include_subjects(sub_list, subject_ids):
#     new_list =

def get_vars(list, subject_id, session_id, run_id):
    return list[subject_id+"_"+session_id+"_"+run_id]

from .anatomical import anat_qc_workflow_dhcp
def ms_anat_dhcp(settings=None, subject_id=None, session_id=None, run_id=None):
    """ Multi-subject anatomical workflow wrapper """
    # Run single subject mode if only one subject id is provided
    if subject_id is not None and isinstance(subject_id, string_types):
        subject_id = [subject_id]

    import json
    import pandas as pd
    with open(settings['qc_measures'], 'r') as jsondata:
        json_list = json.load(jsondata)
        sub_list = pd.DataFrame(json_list['data'])

    if subject_id is not None:
        sub_list = sub_list.loc[sub_list['subject_id'] == subject_id]
    if session_id is not None:
        sub_list = sub_list.loc[sub_list['session_id'] == session_id]
    if run_id is not None:
        sub_list = sub_list.loc[sub_list['run_id'] == run_id]

    if sub_list.empty:
        raise RuntimeError('No scans found in %s' % settings['dhcp_data'])

    data_list = []
    data_list_info = {}
    for d, i in sub_list.iterrows(): 
        data_list.append((i['subject_id'], i['session_id'], i['run_id']))
        data_list_info[i['subject_id']+"_"+i['session_id']+"_"+i['run_id']] = (i['reorient'])

    inputnode = pe.Node(niu.IdentityInterface(fields=['subject_id', 'session_id', 'run_id']), name='inputnode')
    inputnode.synchronize = True
    inputnode.iterables = [('subject_id', 'session_id', 'run_id'), data_list]

    anat_qc = anat_qc_workflow_dhcp(settings=settings)
    anat_qc.inputs.inputnode.bids_root = settings['bids_root']
    sub_vars = pe.Node(niu.Function(input_names=['list','subject_id', 'session_id', 'run_id'], 
                                output_names=[ 'reorient' ], 
                                function=get_vars), name='vars')
    sub_vars.inputs.list = data_list_info
    
    workflow = pe.Workflow(name='anatMRIQC')
    workflow.connect([
        (inputnode, sub_vars, [('subject_id', 'subject_id'), ('session_id', 'session_id'), ('run_id', 'run_id')]),
        (inputnode, anat_qc, [('subject_id', 'inputnode.subject_id'), ('session_id', 'inputnode.session_id'), ('run_id', 'inputnode.run_id')]),
        (sub_vars, anat_qc, [('reorient', 'inputnode.reorient') ])
    ])

    return workflow


def ms_anat(settings=None, subject_id=None, session_id=None, run_id=None):
    """ Multi-subject anatomical workflow wrapper """
    # Run single subject mode if only one subject id is provided
    if subject_id is not None and isinstance(subject_id, string_types):
        subject_id = [subject_id]

    sub_list = gather_bids_data(settings['bids_root'],
                                subject_inclusion=subject_id,
                                include_types=['anat'])

    if session_id is not None:
        sub_list = [s for s in sub_list if s[1] == session_id]
    if run_id is not None:
        sub_list = [s for s in sub_list if s[2] == run_id]

    if not sub_list:
        raise RuntimeError('No scans found in %s' % settings['bids_root'])

    inputnode = pe.Node(niu.IdentityInterface(fields=['data']),
                        name='inputnode')
    inputnode.iterables = [('data', [list(s) for s in sub_list])]
    anat_qc = anat_qc_workflow(settings=settings)
    anat_qc.inputs.inputnode.bids_root = settings['bids_root']

    dsplit = pe.Node(niu.Split(splits=[1, 1, 1], squeeze=True),
                     name='datasplit')
    workflow = pe.Workflow(name='anatMRIQC')
    workflow.connect([
        (inputnode, dsplit, [('data', 'inlist')]),
        (dsplit, anat_qc, [('out1', 'inputnode.subject_id'),
                           ('out2', 'inputnode.session_id'),
                           ('out3', 'inputnode.run_id')])
    ])

    return workflow


def ms_func(settings=None, subject_id=None, session_id=None, run_id=None):
    """ Multi-subject functional workflow wrapper """
    # Run single subject mode if only one subject id is provided
    if subject_id is not None and isinstance(subject_id, string_types):
        subject_id = [subject_id]

    sub_list = gather_bids_data(settings['bids_root'],
                                subject_inclusion=subject_id,
                                include_types=['func'])
    if session_id is not None:
        sub_list = [s for s in sub_list if s[1] == session_id]
    if run_id is not None:
        sub_list = [s for s in sub_list if s[2] == run_id]

    if not sub_list:
        raise RuntimeError('No scans found in %s' % settings['bids_root'])

    inputnode = pe.Node(niu.IdentityInterface(fields=['data']),
                        name='inputnode')
    inputnode.iterables = [('data', [list(s) for s in sub_list])]
    func_qc = fmri_qc_workflow(settings=settings)
    func_qc.inputs.inputnode.bids_root = settings['bids_root']
    func_qc.inputs.inputnode.start_idx = settings.get('start_idx', 0)
    func_qc.inputs.inputnode.stop_idx = settings.get('stop_idx', None)

    dsplit = pe.Node(niu.Split(splits=[1, 1, 1], squeeze=True),
                     name='datasplit')
    workflow = pe.Workflow(name='funcMRIQC')
    workflow.connect([
        (inputnode, dsplit, [('data', 'inlist')]),
        (dsplit, func_qc, [('out1', 'inputnode.subject_id'),
                           ('out2', 'inputnode.session_id'),
                           ('out3', 'inputnode.run_id')])
    ])

    return workflow
