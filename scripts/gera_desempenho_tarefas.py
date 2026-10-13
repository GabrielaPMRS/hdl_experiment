"""Plot full-task execution times and attempts, using every collected participant."""
import argparse
import json
import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np
import pandas as pd
import seaborn as sns

from caminhos import raiz_dados
from selecao_participantes import seleciona_nomes
from plot_common import VERSIONS, TASKS, LABELS, COLORS, case_label


def load_sessions(collections, *, apply_selection=True):
    rows, sources = [], []
    folders = {p.name: p for p in collections.glob('P*')
               if p.is_dir() and re.fullmatch(r'P\d+', p.name)}
    names = seleciona_nomes(folders) if apply_selection else sorted(folders)
    for name in names:
        folder = folders[name]
        if not folder.is_dir() or not re.fullmatch(r'P\d+', folder.name):
            continue
        path = folder / f'resultado{folder.name}.json'
        session = json.loads(path.read_text(encoding='utf-8-sig'))
        if isinstance(session, list):
            if len(session) != 1:
                raise ValueError(f'Expected exactly one session: {path}')
            session = session[0]
        version = session['versaoExperimento'].lower()
        expected = 'lambda' if int(folder.name[1:]) % 2 == 0 else 'omega'
        questions = session['perguntas']
        if (session['participanteId'] != folder.name or version != expected
                or len(questions) != 4
                or {q['codigoId'] for q in questions} != {'code-1','code-2','code-4','code-5'}
                or {q['ordemExecucao'] for q in questions} != {1,2,3,4}):
            raise ValueError(f'Inconsistent session: {path}')
        for q in questions:
            seconds, attempts = q['segundos'], q['tentativas']
            if (type(seconds) not in (int, float) or not np.isfinite(seconds) or seconds <= 0
                    or type(attempts) is not int or attempts < 1):
                raise ValueError(f'Invalid time or attempts: {path}, {q["codigoId"]}')
            rows.append(dict(Participant=folder.name, Condition=LABELS[version],
                Task=f'T{int(q["codigoId"].split("-")[-1]):02}',
                ExecutionTimeSeconds=float(seconds), Attempts=attempts))
        sources.append(dict(Participant=folder.name, Condition=LABELS[version], Source=str(path.resolve())))
    if not rows or {r['Condition'] for r in rows} != set(LABELS.values()):
        raise ValueError('Complete sessions from both conditions are required.')
    return pd.DataFrame(rows), pd.DataFrame(sources)


def plot_distribution(data, task, metric, output, dpi, y_limits=None):
    """Estimate time KDE in log space; attempts remain on a linear scale."""
    subset = data.copy() if task is None else data.loc[data.Task == task].copy()
    is_time = metric == 'ExecutionTimeSeconds'
    subset['PlotValue'] = np.log10(subset[metric]) if is_time else subset[metric]
    order = list(LABELS.values())
    fig, ax = plt.subplots(figsize=(7.4, 6), layout='constrained')
    sns.violinplot(data=subset, x='Condition', y='PlotValue', hue='Condition',
        order=order, hue_order=order, palette=COLORS, inner=None, cut=2 if is_time else 0,
        bw_adjust=.8, density_norm='width', linewidth=1.1, saturation=.75,
        alpha=.55, legend=False, ax=ax)
    sns.boxplot(data=subset, x='Condition', y='PlotValue', order=order,
        width=.14, showfliers=False, color='white',
        boxprops={'facecolor': '#ffffff88', 'edgecolor': '#333333'},
        medianprops={'color': '#222222', 'linewidth': 2}, ax=ax)
    # A fixed seed makes the display reproducible without changing measurements.
    rng = np.random.default_rng(2026)
    for index, label in enumerate(order):
        values = subset.loc[subset.Condition == label, 'PlotValue']
        ax.scatter(index + rng.uniform(-.09, .09, len(values)), values,
                   s=32, c='#333333', alpha=.75, edgecolors='white', linewidths=.4, zorder=4)
    name = 'Execution time' if is_time else 'Attempts'
    units = ' s' if is_time else ''
    totals = subset.groupby('Condition')[metric].sum()
    counts = subset.groupby('Condition').Participant.nunique()
    fmt = '.1f' if is_time else '.0f'
    scope = 'All four tasks — Per-participant total' if task is None else case_label(task)
    ax.set_title(f'{scope} — {name}\n' + '\n'.join(
        f'{label}: total {totals[label]:{fmt}}{units} (n={counts[label]})' for label in order),
        fontsize=13, pad=14)
    ax.set_xlabel('')
    ax.set_ylabel(('Total execution time' if task is None else 'Execution time') + ' (seconds, log scale)'
                  if is_time else ('Total attempts across four tasks' if task is None else 'Attempts') + ' (including correct attempts)')
    if is_time:
        low, high = ax.get_ylim()
        ticks = [np.log10(m * 10.0 ** e) for e in range(-2, 7) for m in (1, 2, 5)
                 if low <= np.log10(m * 10.0 ** e) <= high]
        ax.set_yticks(ticks)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{10 ** value:g}'))
    else:
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        if y_limits is not None:
            ax.set_ylim(*y_limits)
        else:
            ax.set_ylim(bottom=max(0, ax.get_ylim()[0]))
    sns.despine(ax=ax)
    fig.savefig(output, dpi=dpi)
    plt.close(fig)


def participant_totals(data, metric):
    """Each observation is one participant's sum across the four distinct tasks."""
    groups = data.groupby(['Participant', 'Condition'])
    if data.duplicated(['Participant','Task']).any() or any(
            set(group.Task) != set(TASKS) for _, group in groups):
        raise ValueError('Each participant must have exactly the four distinct tasks.')
    return groups[metric].sum().reset_index()


def generate(data, sources, output, metrics, dpi):
    sns.set_theme(style='whitegrid', font_scale=1.05)
    for metric, slug in metrics:
        folder = output / slug
        folder.mkdir(parents=True, exist_ok=True)
        data[['Participant','Condition','Task',metric]].to_csv(folder/'participant_task_values.csv', index=False)
        sources.to_csv(folder/'sources.csv', index=False)
        summary = data.groupby(['Task','Condition'])[metric].agg(
            Participants='count', Total='sum', Mean='mean', Median='median', SD='std', Minimum='min', Maximum='max')
        summary.to_csv(folder/'summary.csv')
        totals = participant_totals(data, metric)
        y_limits = None
        total_y_limits = None
        if metric == 'Attempts':
            y_limits = (0, int(np.ceil(float(data[metric].max()) * 1.08)))
            total_y_limits = (0, int(np.ceil(float(totals[metric].max()) * 1.08)))
        for task in TASKS:
            plot_distribution(data, task, metric, folder/f'{task.lower()}_violin.png', dpi, y_limits)
        totals.to_csv(folder/'participant_totals.csv', index=False)
        totals.groupby('Condition')[metric].agg(
            Participants='count', Total='sum', Mean='mean', Median='median', SD='std',
            Minimum='min', Maximum='max').to_csv(folder/'overall_summary.csv')
        plot_distribution(totals, None, metric, folder/'all_tasks_violin.png', dpi, total_y_limits)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coletas-dir', type=Path, default=raiz_dados()/'coletas')
    parser.add_argument('--output-dir', type=Path, default=raiz_dados()/'graficos/agregados')
    parser.add_argument('--dpi', type=int, default=300)
    args = parser.parse_args()
    data, sources = load_sessions(args.coletas_dir)
    generate(data, sources, args.output_dir,
             [('ExecutionTimeSeconds','execution_time'), ('Attempts','attempts')], args.dpi)
    print(f'Figures saved to {args.output_dir}')


if __name__ == '__main__':
    main()
