"""Describe baseline experience balance, counting each participant once."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from caminhos import raiz_dados
from gera_desempenho_tarefas import load_sessions

FIELDS = {
    'experienciaAnos': ('SystemVerilog experience', ['1 ou menos','2','3','4','5 ou mais'], ['≤1 year','2 years','3 years','4 years','≥5 years']),
    'proficiencia': ('Self-rated SystemVerilog proficiency', ['Novato','Iniciante','Intermediário','Avançado','Especialista'], ['Novice','Beginner','Intermediate','Advanced','Expert']),
    'experienciaHardware': ('Hardware experience', ['Sem experiência','Menos de 1 ano','1 a 2 anos','3 a 5 anos','6 a 10 anos','Mais de 10 anos'], ['None','<1 year','1–2 years','3–5 years','6–10 years','>10 years']),
    'experienciaSoftware': ('Software programming experience', ['Sem experiência','Menos de 1 ano','1 a 2 anos','3 a 5 anos','6 a 10 anos','Mais de 10 anos'], ['None','<1 year','1–2 years','3–5 years','6–10 years','>10 years']),
    'areaExperiencia': ('Main experience setting', ['Acadêmica','Profissional'], ['Academic','Professional']),
}
CONDITIONS = ['With Atom','Without Atom']


def analyze(collections, output):
    _, sources = load_sessions(collections)
    rows = []
    for source in sources.to_dict('records'):
        session = json.loads(Path(source['Source']).read_text(encoding='utf-8-sig'))
        if isinstance(session, list):
            session = session[0]
        demographic = session.get('demografia', {})
        row = {key: source[key] for key in ('Participant','Condition')}
        for key, (_, categories, _) in FIELDS.items():
            answer = demographic.get(key)
            if answer not in categories:
                raise ValueError(f'Unexpected/missing answer: {source["Participant"]}/{key}: {answer}')
            row[key] = answer
        rows.append(row)
    data = pd.DataFrame(rows)
    output.mkdir(parents=True, exist_ok=True)
    data.to_csv(output/'participant_experience.csv', index=False)
    frequencies = []
    report = ['# Equilíbrio de experiência entre as condições', '',
        'Fonte: respostas demográficas dos JSONs originais em `coletas`. Cada participante é contado uma única vez, independentemente das quatro tarefas e de recuperações oculares.', '',
        'With Atom = lambda; Without Atom = omega. Não há exclusões ou respostas ausentes nos cinco campos analisados.', '']
    fig, axes = plt.subplots(5, 1, figsize=(11, 15), layout='constrained')
    colors = ['#d8e4ee','#a8c7dd','#72a7c8','#4284af','#24597e','#163b56']
    for ax, (field, (label, categories, translations)) in zip(axes, FIELDS.items()):
        report += [f'## {label}', '', '| Resposta | With Atom | Without Atom | Diferença (p.p.) |', '|---|---:|---:|---:|']
        left = [0., 0.]
        for index, (category, translation) in enumerate(zip(categories, translations)):
            counts, percentages = [], []
            for condition in CONDITIONS:
                group = data.loc[data.Condition == condition]
                count = int((group[field] == category).sum())
                pct = 100 * count / len(group)
                counts.append(count); percentages.append(pct)
                frequencies.append(dict(Variable=label, Response=translation, Condition=condition,
                                        Count=count, Participants=len(group), Percent=pct))
            report.append(f'| {category} | {counts[0]} ({percentages[0]:.1f}%) | {counts[1]} ({percentages[1]:.1f}%) | {percentages[0]-percentages[1]:+.1f} |')
            bars = ax.barh(CONDITIONS, percentages, left=left, color=colors[index], label=translation, height=.48)
            for bar, count in zip(bars, counts):
                if count:
                    ax.text(bar.get_x()+bar.get_width()/2, bar.get_y()+bar.get_height()/2,
                            str(count), ha='center', va='center', color='white' if index >= 3 else '#172b3b', fontsize=11)
            left = [a+b for a,b in zip(left,percentages)]
        ax.invert_yaxis()
        ax.set_xlim(0,100)
        ax.set_title(label, loc='left', fontsize=13, pad=10)
        ax.set_xticks([0,25,50,75,100], ['0%','25%','50%','75%','100%'])
        ax.spines[['top','right']].set_visible(False)
        ax.legend(loc='upper center', bbox_to_anchor=(.5,-.2), ncol=3, frameon=False, fontsize=9)
        report.append('')
    fig.suptitle('Participant experience by condition (n=13 per group)\nBar labels indicate participant counts', fontsize=16)
    fig.savefig(output/'experience_balance.png', dpi=200)
    plt.close(fig)
    pd.DataFrame(frequencies).to_csv(output/'experience_frequencies.csv', index=False)
    report += ['## Interpretação', '',
        'Os grupos têm o mesmo tamanho e perfis muito semelhantes em experiência específica de SystemVerilog e proficiência autodeclarada. O balanceamento não é completo em experiência geral: Without Atom tem mais participantes com pelo menos seis anos de programação (5/13 contra 2/13) e pelo menos três anos de hardware (6/13 contra 4/13). With Atom tem mais participantes de atuação profissional (3/13 contra 1/13).', '',
        'Essa diferença de experiência pode influenciar o desempenho, mas a descrição não demonstra que explique as diferenças de tempo, tentativas ou fixações. As respostas são faixas ordenadas e autodeclaradas: não foram convertidas em médias artificiais de anos, sobretudo nas categorias abertas (≤1 e >10).', '',
        'Conclusão: boa semelhança na experiência específica de HDL; desequilíbrio descritivo em experiência geral, principalmente software. Igualdade de tamanho não implica equivalência de perfis. Com 13 pessoas por grupo, uma pessoa corresponde a 7,7 pontos percentuais. Não se usa ausência de significância estatística como prova de balanceamento.', '',
        'Para o artigo, apresentar as distribuições e reconhecer a experiência geral como possível fator de confusão. Uma análise de sensibilidade pode verificar se o contraste entre condições se mantém ao considerar a experiência em software, evitando muitos ajustes simultâneos em uma amostra pequena.']
    (output/'experience_balance.md').write_text('\n'.join(report)+'\n')
    print('\n'.join(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--coletas-dir', type=Path, default=raiz_dados()/'coletas')
    parser.add_argument('--output-dir', type=Path, default=raiz_dados()/'graficos/agregados/experience_balance')
    args = parser.parse_args()
    analyze(args.coletas_dir, args.output_dir)
