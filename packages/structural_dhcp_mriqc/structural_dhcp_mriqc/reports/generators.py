#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
# pylint: disable=no-member
#
# @Author: oesteban
# @Date:   2016-01-05 11:33:39
# @Email:  code@oscaresteban.es
# @Last modified by:   oesteban
# @Last Modified time: 2016-05-20 09:10:18
""" Encapsulates report generation functions """

import sys
import os
import os.path as op
import collections
import glob
import json

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import jinja2

from ..interfaces.viz_utils import plot_measures, plot_all, plot_mosaic

# matplotlib.rc('figure', figsize=(11.69, 8.27))  # for DINA4 size
STRUCTURAL_QCGROUPS = [
    # ['icvs_csf', 'icvs_gm', 'icvs_wm'],
    # ['rpve_csf', 'rpve_gm', 'rpve_wm'],
    ['snr', 'snr_csf', 'snr_gm', 'snr_wm'],
    ['cnr'], 
    # ['fber'], 
    ['fwhm_avg', 'fwhm_x', 'fwhm_y', 'fwhm_z'],
    ['efc'], 
    ['cjv'],
    # ['qi1', 'qi2'],
    ['inu_range', 'inu_med'],
    ['summary_mean_bg', 'summary_stdv_bg', 'summary_p05_bg', 'summary_p95_bg',
     'summary_mean_csf', 'summary_stdv_csf', 'summary_p05_csf', 'summary_p95_csf',
     'summary_mean_gm', 'summary_stdv_gm', 'summary_p05_gm', 'summary_p95_gm',
     'summary_mean_wm', 'summary_stdv_wm', 'summary_p05_wm', 'summary_p95_wm']
]

STRUCTURAL_DHCP_QCGROUPS = [
    ['volume_brain', 'volume_csf', 'volume_gm', 'volume_wm'],
    ['surface_area'], ['gyrification_index'], ['thickness']
]

version = 1.0
# def workflow_mosaic(info, settings=None):
#     for d, i in info.iterrows(): 
#         if 'reorient' in i:
#             in_file  = i['reorient']
#             if in_file == "": continue

#             subid = i['subject_id']
#             sesid = i['session_id']
#             scanid = i['run_id']
#             out_file = op.join(settings['work_dir'], 'anatomical_%s_%s_%s.pdf' % (subid, sesid, scanid))

#             if os.path.exists(out_file): continue

#             title = 'Volume, subject %s (%s_%s)' % (subid, sesid, scanid)
#             fig = plot_mosaic(in_file, title=title)
#             fig.savefig(out_file, dpi=300)



def workflow_report(qctype, settings=None):
    """ Creates the report """
    import datetime

    with open(settings['qc_measures'], 'r') as jsondata: 
        datalist=json.load(jsondata)["data"]

    out_csv = op.join(settings['output_dir'], 'image_QC_measures.csv')
    dframe = generate_csv_from_json_list(datalist, qctype, settings, out_csv)
    if dframe.empty: raise RuntimeError('Problem with %s' % settings['qc_measures'])
    sub_list = sorted(pd.unique(dframe.subject_id.ravel())) #pylint: disable=E1101


    # workflow_mosaic(dframe, settings)


    qctype = 'anatomical'
    qctype2 = ''
    if settings['dhcp_measures'] != None:
        qctype2 = 'structural_dhcp'
        
    out_dir = settings.get('output_dir', os.getcwd())
    work_dir = settings.get('work_dir', op.abspath('tmp'))
    out_file = op.join(out_dir, qctype + '_%s.pdf')

    result = {}
    func = getattr(sys.modules[__name__], 'report_' + qctype)

    func2 = None
    dframe2 = None
    if qctype2 != '':
        with open(settings['dhcp_measures'], 'r') as jsondata: 
            datalist=json.load(jsondata)["data"]
        out_csv = op.join(settings['output_dir'], 'pipeline_QC_measures.csv')
        dframe2 = generate_csv_from_json_list(datalist, qctype2, settings, out_csv)
        func2 = getattr(sys.modules[__name__], 'report_' + qctype2)

    # Generate summary page
    out_sum = op.join(out_dir, '%s_group.pdf' % qctype)
    summary_cover(dframe, qctype, dframe2, out_file=out_sum)

    # Add histograms
    pdf_group = []
    out_stats = op.join(work_dir, 'stats_group.pdf')
    write_histograms(dframe, dframe2, out_file=out_stats)
    pdf_group.append(out_stats)

    # Generate group report
    qc_group = op.join(work_dir, 'qc_measures_group.pdf')
    # Generate violinplots. If successfull, add documentation.
    func(dframe, out_file=qc_group)
    pdf_group.append(qc_group)


    if qctype2 != '':
        # Generate group report dhcp
        qc_group = op.join(work_dir, 'qc_measures_group_dhcp.pdf')
        # Generate violinplots. If successfull, add documentation.
        func2(dframe2, out_file=qc_group)
        pdf_group.append(qc_group)


    if len(pdf_group) > 0:
        out_group_file = op.join(out_dir, '%s_group_stats.pdf' % qctype)
        # Generate final report with collected pdfs in plots
        concat_pdf(pdf_group, out_group_file)
        result['group'] = {'success': True, 'path': out_group_file}

    out_indiv_files = []
    # Generate individual reports for subjects
    for subid in sub_list:
        # Get subject-specific info
        subdf = dframe.loc[dframe['subject_id'] == subid]
        sessions = sorted(pd.unique(subdf.session_id.ravel()))
        plots = []
        sess_scans = []
        # Re-build mosaic location
        for sesid in sessions:
            sesdf = subdf.loc[subdf['session_id'] == sesid]
            scans = sorted(pd.unique(sesdf.run_id.ravel()))

            # Each scan has a volume and (optional) fd plot
            for scanid in scans:
                fpdf = op.join(work_dir, 'anatomical_%s_%s_%s.pdf' %
                               (subid, sesid, scanid))

                if op.isfile(fpdf):
                    plots.append(fpdf)

                fpdf = op.join(work_dir, 'structural_dhcp_%s_%s_%s.pdf' %
                               (subid, sesid, scanid))

                if op.isfile(fpdf):
                    plots.append(fpdf)

            sess_scans.append('%s (%s)' % (sesid, ', '.join(scans)))

        # Summary cover
        # sfailed = []
        # if failed:
        #     sfailed = ['%s (%s)' % (s[1], s[2])
        #                for s in failed if subid == s[0]]
        out_sum = op.join(work_dir, '%s_summary_%s.pdf' % (qctype, subid))
        summary_cover(dframe, qctype, dframe2, sub_id=subid, out_file=out_sum)
        plots.insert(0, out_sum)

        # Summary (violinplots) of QC measures
        qc_ms = op.join(work_dir, '%s_measures_%s.pdf' % (qctype, subid))

        func(dframe, subject=subid, out_file=qc_ms)
        plots.append(qc_ms)

        # Summary (violinplots) of QC measures dhcp
        if qctype2 != '':
            qc_ms = op.join(work_dir, '%s_measures_%s.pdf' % (qctype2, subid))

            func2(dframe2, subject=subid, out_file=qc_ms)
            plots.append(qc_ms)


        if len(plots) > 0:
            # Generate final report with collected pdfs in plots
            sub_path = out_file % subid
            concat_pdf(plots, sub_path)
            out_indiv_files.append(sub_path)
            result[subid] = {'success': True, 'path': sub_path}
    return out_group_file, out_indiv_files, result








def summary_cover(dframe, qctype, pipeline_frame, failed=None, sub_id=None, out_file=None):
    """ Generates a cover page with subject information """
    global version
    import datetime
    import numpy as np
    from structural_dhcp_rst2pdf.createpdf import RstToPdf
    import pkg_resources as pkgr

    if failed is None:
        failed = []

    newdf = dframe.copy()
    if sub_id is not None:
        newdf = newdf[newdf.subject_id.astype('unicode') == sub_id]

    if 'exists' in newdf:
        for col in ['size_x', 'size_y', 'size_z','spacing_x', 'spacing_y', 'spacing_z']:
            newdf.loc[newdf['exists'] == 'False', col] = pd.Series( 0 , index=newdf.index)
    # Format the size
    #pylint: disable=E1101
    newdf[['size_x', 'size_y', 'size_z']] = newdf[['size_x', 'size_y', 'size_z']].astype(np.uint16)
    #formatter = lambda row: ur'%d \u00D7 %d \u00D7 %d' % (
    formatter = lambda row: r'%d x %d x %d' % (
        row['size_x'], row['size_y'], row['size_z'])
    newdf['size'] = newdf[['size_x', 'size_y', 'size_z']].apply(formatter, axis=1)

    # Format spacing
    newdf[['spacing_x', 'spacing_y', 'spacing_z']] = newdf[[
        'spacing_x', 'spacing_y', 'spacing_z']].astype(np.float32)  #pylint: disable=E1101
    #formatter = lambda row: ur'%.3f \u00D7 %.3f \u00D7 %.3f' % (
    formatter = lambda row: r'%.3f x %.3f x %.3f' % (
        row['spacing_x'], row['spacing_y'], row['spacing_z'])
    newdf['spacing'] = newdf[['spacing_x', 'spacing_y', 'spacing_z']].apply(formatter, axis=1)

    # columns
    cols = ['session_id', 'run_id', 'size', 'spacing']
    colnames = ['Session', ' Scan ', 'Size', 'Spacing']
    if 'tr' in newdf.columns.ravel():
        cols.append('tr')
        colnames.append('TR (sec)')
    if 'size_t' in newdf.columns.ravel():
        cols.append('size_t')
        colnames.append(r'\# Timepoints')

    # Format parameters table
    if sub_id is None:
        cols.insert(0, 'subject_id')
        colnames.insert(0, 'Subject')

    if 'exists' in newdf:
        for col in ['size', 'spacing']:
            newdf.loc[newdf['exists'] == 'False', col] = pd.Series('missing', index=newdf.index)

    newdf = newdf[cols]

    colsizes = []
    for col, colname in zip(cols, colnames):
        newdf[[col]] =newdf[[col]].astype('unicode')
        colsize = newdf.loc[:, col].map(len).max()
        colsizes.append(colsize if colsize > len(colname) else len(colname))

    colformat = u' '.join(u'{:<%d}' % c for c in colsizes)
    formatter = lambda row: colformat.format(*row)
    rowsformatted = newdf[cols].apply(formatter, axis=1).ravel().tolist()
    # rowsformatted = [formatter.format(*row) for row in newdf.iterrows()]
    header = colformat.format(*colnames)
    sep = colformat.format(*['=' * c for c in colsizes])
    ptable = '\n'.join([sep, header, sep] + rowsformatted + [sep])

    title = 'dHCP MRIQC: %s MRI %s report' % (qctype, 'group' if sub_id is None else 'individual')


    pipeline_table = ''
    if pipeline_frame is not None:
        # cols = ['session_id', 'segOK', 'LwhiteOK', 'LinflatedOK', 'LsphereOK', 'RwhiteOK', 'RinflatedOK', 'RsphereOK']
        # colnames = ['Session', 'seg', 'L white', 'L inflated', 'L sphere', 'R white', 'R inflated', 'R sphere' ]
        cols = ['session_id', 'segOK', 'LhemiOK', 'RhemiOK', 'QCOK']
        colnames = ['Session', 'Segmentation', 'L hemisphere', 'R hemisphere', '   QC   ']
        if sub_id is None:
            cols.insert(0, 'subject_id')
            colnames.insert(0, 'Subject')
        else:
            pipeline_frame = pipeline_frame.loc[pipeline_frame.subject_id.astype('unicode') == sub_id]
        if len(pipeline_frame)>0:
            pipeline_frame = pipeline_frame[cols]
            pipeline_frame = pipeline_frame.replace({'True': 'Pass'}, regex=True)
            pipeline_frame = pipeline_frame.replace({'False': 'Fail'}, regex=True)

            colsizes = []
            for col, colname in zip(cols, colnames):
                pipeline_frame[[col]] =pipeline_frame[[col]].astype('unicode')
                colsize = pipeline_frame.loc[:, col].map(len).max()
                colsizes.append(colsize if colsize > len(colname) else len(colname))

            colformat = u' '.join(u'{:<%d}' % c for c in colsizes)
            formatter = lambda row: colformat.format(*row)
            rowsformatted = pipeline_frame[cols].apply(formatter, axis=1).ravel().tolist()
            header = colformat.format(*colnames)
            sep = colformat.format(*['=' * c for c in colsizes])
            pipeline_table = '\n'.join([sep, header, sep] + rowsformatted + [sep])


    # Substitution dictionary
    context = {
        'title': title + '\n' + ''.join(['='] * len(title)),
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d, %H:%M"),
        'version': version,
        # 'failed': failed,
        'imparams': ptable,
        'pipeparams': pipeline_table
    }

    if sub_id is not None:
        context['sub_id'] = sub_id

    if sub_id is None:
        template = ConfigGen(pkgr.resource_filename(
            'structural_dhcp_mriqc', op.join('data', 'reports', 'cover_group.rst')))
    else:
        template = ConfigGen(pkgr.resource_filename(
            'structural_dhcp_mriqc', op.join('data', 'reports', 'cover_individual.rst')))

    RstToPdf().createPdf(
        text=template.compile(context), output=out_file, compressed=True)




def write_histograms(qcframe, dhcpframe, out_file='report.pdf', figsize=(11.69, 5)):
    import numpy as np
    import seaborn as sns
    import matplotlib.gridspec as gridspec
    import datetime

    global version
    title = 'dHCP MRIQC: anatomical MRI group report'
    text="- Date and time: "+str(datetime.datetime.now().strftime("%Y-%m-%d, %H:%M"))+"\n"
    text+="- dHCP MRIQC version: "+str(version)
    report = PdfPages(out_file)

    fig = plt.figure(figsize=(figsize[0],2))
    ax = fig.add_axes([0,0,1,1])
    ax.text(.1, .5, text,
        horizontalalignment='left',
        verticalalignment='center',
        fontsize=16, 
        transform=ax.transAxes)
    ax.set_axis_off()
    fig.suptitle(title, fontsize=20, x=0.1, horizontalalignment='left')  
    plt.show()
    report.savefig(fig, dpi=300)


    numplots = 3
    fig = plt.figure(figsize=figsize, facecolor='white')
    gsp = gridspec.GridSpec(1, numplots)
       
    sns.axes_style('white')
    sns.set_style('white')
    colors = ['blue','red']
    plt.ticklabel_format(style='sci', axis='y', scilimits=(-1, 1))

    axes = []
    for i in range(numplots):
        if i==0:
            total_subjs = len(np.unique(qcframe['subject_id']))
            T1 = len(qcframe.loc[(qcframe['run_id'] == 'T1') & (qcframe['exists'] == 'True')])
            T2 = len(qcframe.loc[(qcframe['run_id'] == 'T2') & (qcframe['exists'] == 'True')])
            total = len(dhcpframe)
            x = ['Subjects', 'Sessions', 'T1', 'T2']
            y = [total_subjs, total, T1, T2]
            title = 'Number of scans'
        elif i==1:
            segOK = len(dhcpframe.loc[dhcpframe['segOK'] == 'True'])
            LhemiOK = len(dhcpframe.loc[dhcpframe['LhemiOK'] == 'True'])
            RhemiOK = len(dhcpframe.loc[dhcpframe['RhemiOK'] == 'True'])
            hemiOK = len(dhcpframe.loc[(dhcpframe['LhemiOK'] == 'True') & (dhcpframe['RhemiOK'] == 'True')])
            QCOK = len(dhcpframe.loc[dhcpframe['QCOK'] == 'True'])
            x = ['Segmentation', 'L hemisphere', 'R hemisphere','Both hemispheres','QC']
            y = [segOK, LhemiOK, RhemiOK, hemiOK, QCOK]
            title = 'Pipeline steps completed'
        elif i==2:
            ages = np.round(dhcpframe['age'].astype(np.float32).values).astype(np.int)
            iages = np.unique(ages)
            x=[]
            y=[]
            for age in iages:
                x.append(str(age))
                y.append(len(np.where(ages == age)[0]))
            title = 'Age at scan (weeks)'

        axes.append(plt.subplot(gsp[i]))
        pal = sns.color_palette("hls", len(x))
        ax = sns.barplot(x, y, ax=axes[-1], linewidth=.8, palette=pal)
        ax.set_title(title, fontsize=10)
        ax.set_ylim([0,total*1.1])
        ax.set_yticks([])
        ax.set_xticklabels(
            [el.get_text() for el in axes[-1].get_xticklabels()],
            rotation='vertical')

        for n, (label, _y) in enumerate(zip(x, y)):
            ax.annotate(
                s='{:.0f}'.format(abs(_y)),
                xy=(n, _y),
                ha='center',va='center',
                xytext=(0,10),
                textcoords='offset points',
                weight='bold'
            )

    plt.tight_layout(pad=0.4, w_pad=0.5, h_pad=1.0)
    plt.subplots_adjust(top=0.85)
    plt.show()

    fig.suptitle('Scans statistics')
    report.savefig(fig, dpi=300)
    fig.clf()

    report.close()
    plt.close()
    # print 'Written report file %s' % out_file
    return out_file


def concat_pdf(in_files, out_file='concatenated.pdf'):
    """ Concatenate PDF list (http://stackoverflow.com/a/3444735) """
    from PyPDF2 import PdfFileWriter, PdfFileReader

    with open(out_file, 'wb') as out_pdffile:
        outpdf = PdfFileWriter()

        for in_file in in_files:
            with open(in_file, 'rb') as in_pdffile:
                inpdf = PdfFileReader(in_pdffile)
                for fpdf in range(inpdf.numPages):
                    outpdf.addPage(inpdf.getPage(fpdf))
                outpdf.write(out_pdffile)

    return out_file


def _write_report(dframe, groups, sub_id=None, sc_split=False, condensed=True,
                  out_file='report.pdf'):
    if 'exists' in dframe:
        dframe = dframe[dframe['exists'] == 'True']
    if 'QCOK' in dframe:
        dframe = dframe[dframe['QCOK'] == 'True']


    columns = dframe.columns.ravel()
    headers = []
    for g in groups:
        rem = []
        for h in g:
            if h not in columns:
                rem.append(h)
            else:
                headers.append(h)
        for r in rem:
            g.remove(r)
    report = PdfPages(out_file)

    groupadd = ''
    subadd = ''
    scans = ['']
    if sc_split:
        scans = sorted(pd.unique(dframe.run_id.ravel()))

    for scid in scans:
        if scid == '':
            df = dframe
        else:
            df = dframe.loc[dframe['run_id'] == scid]
            if len(df.index) == 0: continue
            groupadd = '(%s)' % (scid)
            subadd = '_%s' % (scid)

        if sub_id is None:
           if condensed:
                fig = plot_all(df, groups, strip_nsubj=2, title='QC measures '+groupadd)
           else:
                fig = plot_measures(df, headers, title='QC measures '+groupadd)
           report.savefig(fig, dpi=300)
           fig.clf()
        else:         
            subdf = df.copy().loc[df['subject_id'] == sub_id]   
            if len(subdf.index) == 0: continue
            if condensed:
                sessions = sorted(pd.unique(subdf['session_id'].ravel())) 
                for ss in sessions:
                    subtitle = '(subject %s_%s%s)' % (sub_id, ss, subadd)
                    fig = plot_all(df, groups, subject=sub_id, session=ss, strip_nsubj=2, title='QC measures ' + subtitle)
                    report.savefig(fig, dpi=300)
                    fig.clf()
            else:       
                subtitle = '(subject %s%s)' % (sub_id, subadd)
                fig = plot_measures(df, headers, subject=sub_id, title='QC measures ' + subtitle)
                report.savefig(fig, dpi=300)
                fig.clf()

    report.close()
    plt.close()
    # print 'Written report file %s' % out_file
    return out_file


def report_anatomical(
        dframe, subject=None, sc_split=True, condensed=True,
        out_file='anatomical.pdf'):
    """ Calls the report generator on the functional measures """
    return _write_report(dframe, STRUCTURAL_QCGROUPS, sub_id=subject, sc_split=sc_split,
                         condensed=condensed, out_file=out_file)

def report_structural_dhcp(
        dframe, subject=None, sc_split=True, condensed=True,
        out_file='structural_dhcp.pdf'):
    """ Calls the report generator on the functional measures """
    return _write_report(dframe, STRUCTURAL_DHCP_QCGROUPS, sub_id=subject, sc_split=sc_split,
                         condensed=condensed, out_file=out_file)

# def generate_csv(data_type, settings):
#     datalist = []
#     errorlist = []
#     jsonfiles = glob.glob(op.join(settings['work_dir'], 'derivatives', '%s*.json' % data_type))

#     if not jsonfiles:
#         raise RuntimeError('No individual QC files were found in the working directory'
#                            '\'%s\' for the \'%s\' data type.' % (settings['work_dir'], data_type))

#     for jsonfile in jsonfiles:
#         dfentry = _read_and_save(jsonfile)
#         if dfentry is not None:
#             if 'exec_error' not in dfentry.keys():
#                 datalist.append(dfentry)
#             else:
#                 errorlist.append(dfentry['subject_id'])

#     return generate_csv_from_json_list(datalist, data_type, settings), errorlist


def generate_csv_from_json_list(datalist, data_type, settings, out_file):
    dataframe = pd.DataFrame(datalist)
    cols = dataframe.columns.tolist()  # pylint: disable=no-member

    reorder = []
    for field in ['run', 'session', 'subject']:
        for col in cols:
            if col.startswith(field):
                reorder.append(col)

    for col in reorder:
        cols.remove(col)
        cols.insert(0, col)

    if 'mosaic_file' in cols:
        cols.remove('mosaic_file')

    # Sort the dataframe, with failsafe if pandas version is too old
    try:
        dataframe = dataframe.sort_values(by=['subject_id', 'session_id', 'run_id'])
    except AttributeError:
        #pylint: disable=E1101
        dataframe = dataframe.sort(columns=['subject_id', 'session_id', 'run_id'])

    # Drop duplicates
    try:
        #pylint: disable=E1101
        dataframe.drop_duplicates(['subject_id', 'session_id', 'run_id'], keep='last',
                                  inplace=True)
    except TypeError:
        #pylint: disable=E1101
        dataframe.drop_duplicates(['subject_id', 'session_id', 'run_id'], take_last=True,
                                  inplace=True)

    out_fname = out_file;
    dataframe[cols].to_csv(out_fname, index=False)
    return dataframe 


def _read_and_save(in_file):
    with open(in_file, 'r') as jsondata:
        values = _flatten(json.load(jsondata))
        return values
    return None


def _flatten(in_dict, parent_key='', sep='_'):
    items = []
    for k, val in list(in_dict.items()):
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(val, collections.MutableMapping):
            items.extend(_flatten(val, new_key, sep=sep).items())
        else:
            items.append((new_key, val))
    return dict(items)


class ConfigGen(object):
    """
    Utility class for generating a config file from a jinja template.
    https://github.com/oesteban/endofday/blob/f2e79c625d648ef45b08cc1f11fd0bd84342d604/endofday/core/template.py
    """
    def __init__(self, template_str):
        self.template_str = template_str
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(searchpath='/'),
            trim_blocks=True, lstrip_blocks=True)

    def compile(self, configs):
        template = self.env.get_template(self.template_str)
        return template.render(configs)

    def generate_conf(self, configs, path):
        output = self.compile(configs)
        with open(path, 'w+') as output_file:
            output_file.write(output)
