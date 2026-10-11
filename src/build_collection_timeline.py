#!/usr/bin/env python3
"""Study-level chronology; monitoring spans are distinct from audited coverage."""
from pathlib import Path
import hashlib
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as md
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/data_timeline'
AS_OF = '2026-10-11'
BLUE = '#497E9E'
TEAL = '#168783'
GOLD = '#B88936'
PURPLE = '#8570A5'
INK = '#203544'
GREY = '#647684'


def collection_rows():
    hop = pd.read_csv(ROOT / 'data/collections/ndosho/hopmeter/series_inventory.csv')
    survey = json.loads((ROOT / 'outputs/drc2_failure_audit/run_audit.json').read_text())
    count = survey['facility_denominator']
    return [
        dict(dataset='Historical grid and generator records',
             start='2020-01-01', end='2023-12-31', kind='records',
             date_label='2020-2023', qualifier='Master spreadsheet and overlapping 2023 transcription',
             coverage_status='coarse year span; source overlap and mixed day/month dates not reconciled',
             source='data/collections/ndosho/historical/source_manifest.json; data/collections/ndosho/generator_register/source_manifest.json',
             display_style='coarse'),
        dict(dataset='GridWatch monitoring\n(two sensors deployed; one reporting now)',
             start='2022-05-27', end=AS_OF, kind='telemetry',
             date_label='May 2022-Oct 2026', qualifier='Two sensor histories grouped in one monitoring band',
             coverage_status='both returned in installation week and event; M004 returned in October 2026; intervening paired coverage unverified',
             source='data/collections/ndosho/powerwatch/coverage_request.json',
             display_style='monitoring_span'),
        dict(dataset='Event-period generator and fuel register',
             start='2024-12-26', end='2025-03-01', kind='records',
             date_label='Dec 2024-Mar 2025', qualifier='Runtime and fuel entries spanning the January event',
             coverage_status='manual entries and separate model-derived estimates; fuel entries are not measured fuel burn',
             source='data/collections/ndosho/generator_register/source_manifest.json',
             display_style='observed'),
        dict(dataset='HOPmeter monitoring\n(5 L/min concentrator, 10 L/min concentrator,\nneonatology concentrator, whole facility)',
             start=str(hop.first_time_source.min()), end=str(hop.last_time_source.max()), kind='telemetry',
             date_label='Jan 2023-Jan 2024', qualifier='13 load files combined; listed loads are selected examples',
             coverage_status='union of file spans; devices have different coverage, gaps and unverified clock zones',
             source='data/collections/ndosho/hopmeter/series_inventory.csv',
             display_style='observed'),
        dict(dataset='Preliminary oxygen survey (n=18)',
             start='2024-10-08', end='2024-11-04', kind='survey',
             date_label='Oct-Nov 2024', qualifier='Facility and ward oxygen assessment',
             coverage_status='n=18 requested by study lead; 17 dated visits in displayed window, one January 2024 date remains to reconcile',
             source='Valentin thesis, Table 34, printed p. 102; sample label specified by study lead 2026-10-11',
             display_style='observed'),
        dict(dataset=f'Cross-sectional survey (n={count} facilities)',
             start=survey['submission_time_start'], end=survey['submission_time_end'], kind='survey',
             date_label='May-Nov 2025', qualifier='Submission dates; 565 forms / 518 retained respondents',
             coverage_status='facility count from current deduplication; dates are submission timestamps, not verified interview dates',
             source='outputs/drc2_failure_audit/run_audit.json',
             display_style='observed'),
        dict(dataset='Retrospective field interview',
             start='2026-01-27', end='2026-01-27', kind='interview',
             date_label='27 Jan 2026', qualifier='Recorded retrospective account',
             coverage_status='interview date; PSA installation date remains unresolved',
             source='https://docs.google.com/document/d/1TKk1lK1sBN_XpJI80o6OH_NnTJVLZYoZYsAHRBCoRZ8/edit',
             display_style='observed'),
        dict(dataset='Retrospective field interview',
             start='2026-11-01', end='2026-12-01', kind='interview',
             date_label='Nov 2026 - planned', qualifier='Follow-up interview; exact date to be set',
             coverage_status='planned month, not collected data; end is exclusive month boundary',
             source='Study lead requested November 2026 follow-up, 2026-10-11',
             display_style='planned'),
    ]


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = collection_rows()
    pd.DataFrame(rows).to_csv(OUT / 'dataset_time_mapping.csv', index=False)
    colors = dict(telemetry=BLUE, records=GOLD, survey=TEAL, interview=PURPLE)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'text.color': INK, 'xtick.color': GREY,
                         'pdf.fonttype': 42, 'svg.fonttype': 'none'})
    fig = plt.figure(figsize=(18, 8.5), facecolor='white')
    fig.text(.035, .943, 'DRC3a study data and monitoring timeline', fontsize=25, weight='bold')
    fig.text(.035, .9, 'Ndosho electricity and operating records, comparative surveys and follow-up interviews',
             fontsize=12, color=GREY)
    ax = fig.add_axes([.335, .24, .345, .56])
    ax.set_xlim(pd.Timestamp('2019-11-01'), pd.Timestamp('2026-12-31'))
    ax.set_ylim(-.65, len(rows)-.35)
    ax.invert_yaxis()
    ax.set_yticks([])
    ax.xaxis.set_major_locator(md.YearLocator())
    ax.xaxis.set_major_formatter(md.DateFormatter('%Y'))
    ax.grid(axis='x', color='#E4E9ED', lw=.8)
    ax.spines[['left', 'top', 'right']].set_visible(False)
    fig.text(.035, .83, 'Data source / study', fontsize=10, weight='bold', color=GREY)
    fig.text(.708, .83, 'Collection period', fontsize=10, weight='bold', color=GREY)
    for i, row in enumerate(rows):
        if i % 2 == 0:
            ax.axhspan(i-.44, i+.44, color='#F6F8FA', zorder=0)
        start, end = md.date2num(pd.Timestamp(row['start'])), md.date2num(pd.Timestamp(row['end']))
        color = colors[row['kind']]
        style = row['display_style']
        if start == end:
            ax.plot(start, i, 'D', color=color, ms=8, zorder=4)
        else:
            ax.barh(i, end-start, left=start, height=.22,
                    facecolor='white' if style in {'coarse', 'planned'} else color,
                    edgecolor=color, lw=1.3,
                    hatch='////' if style in {'coarse', 'planned'} else None,
                    alpha=.65 if style=='monitoring_span' else 1, zorder=2)
        if style=='monitoring_span':
            # Endpoints show confirmed deployment/current return, not a switch date.
            ax.scatter([start, end], [i, i], s=[35, 35], color=color, zorder=4)
        ax.text(-.038, i, row['dataset'], transform=ax.get_yaxis_transform(),
                ha='right', va='center', fontsize=10.5, linespacing=1.3)
        ax.text(1.08, i-.10, row['date_label'], transform=ax.get_yaxis_transform(),
                ha='left', va='center', fontsize=10.5, weight='bold')
        ax.text(1.08, i+.18, row['qualifier'], transform=ax.get_yaxis_transform(),
                ha='left', va='center', fontsize=8.4, color=GREY)
    ax.axvline(pd.Timestamp('2025-01-27'), color='#E2743E', ls='--', lw=1)
    ax.text(pd.Timestamp('2025-01-27'), -.9, 'Jan 2025 event', ha='center', fontsize=9, color='#C46636')
    fig.legend(handles=[Patch(fc=BLUE, label='Electrical monitoring'),
                        Patch(fc=GOLD, label='Operating records'),
                        Patch(fc=TEAL, label='Survey'),
                        Line2D([], [], marker='D', ls='', color=PURPLE, label='Interview'),
                        Patch(fc='white', ec=PURPLE, hatch='////', label='Planned interview')],
               loc='upper left', bbox_to_anchor=(.03, .177), ncol=5, frameon=False, fontsize=10)
    fig.text(.035, .112, 'Monitoring bands show programme or file spans, not uninterrupted data coverage. Sensor completeness is audited separately.',
             fontsize=10, color=GREY)
    fig.text(.035, .077, 'HOPmeter combines device-specific periods; no files overlap the January 2025 event. November 2026 is planned.',
             fontsize=10, color=GREY)
    fig.text(.035, .042, 'As of 11 October 2026. Source links, date qualifications and sample definitions: dataset_time_mapping.csv.',
             fontsize=9, color=GREY)
    for extension in ['png', 'pdf', 'svg']:
        fig.savefig(OUT / f'drc3a_collection_timeline.{extension}', dpi=160, facecolor='white')
    plt.close(fig)
    provenance = {'as_of': AS_OF, 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'gridwatch_display': 'one monitoring band, two deployed sensors and one current return; no inferred transition date',
                  'historical_register_display': 'master workbook and overlapping 2023 transcription grouped, not treated as independent records',
                  'cross_sectional_sample': '491 facilities in current audited sample',
                  'preliminary_sample': 'n=18 as specified by study lead; date exception retained in mapping',
                  'november_interview': 'planned month, no claimed completed collection'}
    (OUT / 'timeline_provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')


if __name__ == '__main__':
    build()
