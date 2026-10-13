"""Flag potential outliers for investigation; never exclude or alter observations."""
import argparse
from pathlib import Path
import pandas as pd
from caminhos import raiz_dados
from gera_desempenho_tarefas import load_sessions
from selecao_participantes import seleciona_nomes

METRICS = ('ExecutionTimeSeconds',)


def flag_iqr(data, by_condition=True):
    rows = []
    keys = ['Task','Condition'] if by_condition else ['Task']
    for _, group in data.groupby(keys):
        for metric in METRICS:
            values = group[metric]
            q1, q3 = values.quantile([.25,.75], interpolation='linear')
            iqr = q3-q1
            lower, upper = q1-1.5*iqr, q3+1.5*iqr
            sufficient = len(group) >= 4
            for item in group.to_dict('records'):
                value = item[metric]
                candidate = bool(sufficient and (value < lower or value > upper))
                rows.append(dict(Participant=item['Participant'], Condition=item['Condition'],
                    Task=item['Task'], Metric=metric, Value=value, ReferenceN=len(group),
                    Q1=q1, Q3=q3, IQR=iqr, LowerFence=lower, UpperFence=upper,
                    Candidate=candidate,
                    Direction=('High' if value > upper else 'Low') if candidate else '',
                    ReviewNote=('Insufficient reference sample (n<4)' if not sufficient else
                                'Zero IQR; repeated values make this flag especially fragile' if iqr == 0 else ''),
                    Grouping='TaskAndCondition' if by_condition else 'TaskPooledConditions'))
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coletas-dir', type=Path, default=raiz_dados()/'coletas')
    parser.add_argument('--output-dir', type=Path, default=raiz_dados()/'graficos/agregados/outlier_review')
    args = parser.parse_args()
    data, sources = load_sessions(args.coletas_dir, apply_selection=False)
    selected = seleciona_nomes(data.Participant.unique())
    report = ['# Candidatos a outliers — revisão exploratória', '',
        'Nenhum registro foi excluído, alterado ou classificado como erro de coleta.', '',
        'Regra: valores estritamente fora de [Q1 − 1,5 × IQR, Q3 + 1,5 × IQR], com quartis por interpolação linear. Somente tempo de execução de cada tarefa, em segundos na escala original; tentativas não são classificadas. São sinalizados extremos altos e baixos. Grupos com menos de quatro observações não são classificados.', '',
        'A referência principal é cada caso × condição. Uma segunda tabela usa cada caso com as duas condições juntas, para revelar dependência do agrupamento. Nenhuma dessas regras deve servir para apagar automaticamente o efeito que está sendo estudado.', '',
        'IQR zero é assinalado explicitamente: tempos repetidos podem tornar a regra frágil. Isso não comprova anormalidade nem erro. Os limites são exploratórios, especialmente em grupos pequenos.', '']
    for cohort, frame in [('all_participants',data), ('current_selection',data.loc[data.Participant.isin(selected)])]:
        folder=args.output_dir/cohort
        folder.mkdir(parents=True, exist_ok=True)
        frame[['Participant','Condition','Task','ExecutionTimeSeconds']].to_csv(folder/'input_values.csv', index=False)
        sources.loc[sources.Participant.isin(frame.Participant)].to_csv(folder/'sources.csv', index=False)
        results = flag_iqr(frame)
        results.to_csv(folder/'iqr_review.csv', index=False)
        candidates = results.loc[results.Candidate]
        candidates.to_csv(folder/'candidates.csv', index=False)
        pooled = flag_iqr(frame, by_condition=False)
        pooled.to_csv(folder/'iqr_review_pooled.csv', index=False)
        report += [f'## {cohort}', '', f'{frame.Participant.nunique()} participantes; ' +
                   '; '.join(f'{condition}: {n}' for condition,n in frame.groupby('Condition').Participant.nunique().items()) + '.', '',
                   '| Participante | Condição | Caso | Métrica | Valor | Limite ultrapassado | Observação |',
                   '|---|---|---|---|---:|---:|---|']
        for r in candidates.itertuples():
            fence=r.UpperFence if r.Direction=='High' else r.LowerFence
            report.append(f'| {r.Participant} | {r.Condition} | {r.Task} | {r.Metric} | {r.Value:.2f} | {fence:.2f} ({r.Direction}) | {r.ReviewNote} |')
        report += ['', f'{len(candidates)} sinalizações de participante × caso × métrica; '
                   f'{candidates.Participant.nunique()} participantes com pelo menos uma sinalização. '
                   'Uma pessoa pode aparecer em vários casos ou métricas.', '']
    report += ['## Como investigar', '',
        'Conferir o JSON original e anotações de coleta: interrupções, entendimento da tarefa, número de tentativas e eventual falha técnica. Um tempo alto pode ser uma resposta válida à tarefa. Uma perda ocular não invalida automaticamente o tempo do aplicativo. Se houver justificativa de exclusão, registrar o motivo e comparar os resultados com e sem a observação; não escolher exclusões para obter determinado resultado.', '',
        'A tabela descreve observações por caso, não recomenda excluir o participante inteiro. Os CSVs guardam valores e limites sem arredondamento de apresentação. A seleção atual é registrada em input_values.csv e sources.csv; a lista de inclusão não foi modificada.']
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'review.md').write_text('\n'.join(report)+'\n')
    print('\n'.join(report))


if __name__ == '__main__':
    main()
