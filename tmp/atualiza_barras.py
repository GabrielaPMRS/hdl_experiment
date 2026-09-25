from pathlib import Path
p=Path('scripts/gera_tentativas_agregadas.py')
s=p.read_text(encoding='utf-8-sig'); a=s.index('def gera_grafico('); b=s.index('\ndef main():',a)
s=s[:a]+'''def gera_grafico(dados, caminho, dpi):
    fig, ax = plt.subplots(figsize=(10, 6))
    posicoes = np.arange(len(TAREFAS))
    largura = 0.34
    maior_media = 0
    for indice, (versao, cor) in enumerate(zip(VERSOES, ('#cf5f56', '#397faa'))):
        grupo = dados.loc[dados.Versao == versao]
        medias = grupo.groupby('Tarefa').Tentativas.mean().reindex(TAREFAS)
        maior_media = max(maior_media, float(medias.max()))
        n = grupo.Participante.nunique()
        barras = ax.bar(posicoes + (indice - 0.5) * largura, medias,
                        width=largura, color=cor, label=f'{versao.capitalize()} (n={n})', zorder=3)
        ax.bar_label(barras, labels=[f'{valor:.2f}'.replace('.', ',') for valor in medias],
                     padding=5, fontsize=11)
    ax.set_xticks(posicoes, TAREFAS)
    ax.set_xlabel('Tarefa')
    ax.set_ylabel('Média de tentativas por participante')
    ax.set_title('Média de tentativas por tarefa — Lambda e Omega', fontsize=15, pad=16)
    ax.set_ylim(0, max(2, maior_media * 1.22))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis='y', alpha=.2, zorder=0)
    ax.spines[['top', 'right']].set_visible(False)
    ax.legend(frameon=False)
    fig.text(.5, .02, 'As contagens incluem a tentativa correta. Barras representam médias, não totais.',
             ha='center', fontsize=10)
    fig.tight_layout(rect=(0, .05, 1, 1))
    fig.savefig(caminho, dpi=dpi, bbox_inches='tight')
    plt.close(fig)

'''+s[b:];p.write_text(s,encoding='utf-8')
p=Path('scripts/README_AGREGADOS.md');s=p.read_text(encoding='utf-8-sig');s=s.replace('Cada ponto representa um participante; o traco preto e a media; o eixo vertical e comum entre tarefas.', 'Barras agrupadas mostram a media de tentativas por participante, com valores acima das barras e eixo vertical comum entre tarefas.');p.write_text(s,encoding='utf-8')
