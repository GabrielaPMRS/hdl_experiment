# =========================
# Imports
# =========================
import os
import csv
import json
import argparse
import statistics
from itertools import tee

import numpy as np
import pandas as pd
import scipy.stats as st

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.pyplot as pl

import matplotlib.image as mpimg
from matplotlib.collections import LineCollection
from matplotlib.colors import ListedColormap

import seaborn as sns
import PIL

# ============================================================
# Eye-tracking preprocessing
# ============================================================
def remove_missing(x, y, time, missing):
	mx = np.array(x==missing, dtype=int)
	my = np.array(y==missing, dtype=int)
	x = x[(mx+my) != 2]
	y = y[(mx+my) != 2]
	time = time[(mx+my) != 2]
	return x, y, time  

def fixation_detection(x, y, time, missing=0.0, maxdist=25, mindur=200):
	x, y, time = remove_missing(x, y, time, missing)
	Sfix = []
	Efix = []	
	si = 0
	fixstart = False
	for i in range(1,len(x)):
		squared_distance = ((x[si]-x[i])**2 + (y[si]-y[i])**2)
		dist = 0.0
		if squared_distance > 0:
			dist = squared_distance**0.5
		if dist <= maxdist and not fixstart:
			si = 0 + i
			fixstart = True
			Sfix.append([time[i]])
		elif dist > maxdist and fixstart:
			fixstart = False
			if time[i-1]-Sfix[-1][0] >= mindur:
				Efix.append([Sfix[-1][0], time[i-1], time[i-1]-Sfix[-1][0], x[si], y[si]])
			else:
				Sfix.pop(-1)
			si = 0 + i
		elif not fixstart:
			si += 1
	if len(Sfix) > len(Efix):
		Efix.append([Sfix[-1][0], time[len(x)-1], time[len(x)-1]-Sfix[-1][0], x[si], y[si]])
	return Sfix, Efix


# ============================================================
# AOI definitions for each experiment version and task program
# codigo = [pixel_da_base, pixel_do_topo] eixo y
# ============================================================
def carregaConfiguracaoDasAOIs(caminho):
    with open(caminho, encoding="utf-8") as arquivo:
        configuracao = json.load(arquivo)

    for versao in ("lambda", "omega"):
        if versao not in configuracao:
            raise ValueError("Versao ausente no arquivo de AOIs: " + versao)
        for numero in range(1, 7):
            tarefa = "T{0:02d}".format(numero)
            if tarefa not in configuracao[versao]:
                raise ValueError("AOI ausente: " + versao + "/" + tarefa)

    return configuracao


def retornaLimitesDasAOIs(configuracao, versao, imgid):
    try:
        dados = configuracao[versao][imgid]
    except KeyError as erro:
        raise ValueError("AOI nao encontrada: " + versao + "/" + imgid) from erro

    codigo = dados.get("codigo")
    aoi1 = dados.get("aoi1")
    if not isinstance(codigo, list) or len(codigo) != 2 or None in codigo:
        raise ValueError("Limite do codigo incompleto: " + versao + "/" + imgid)
    if not isinstance(aoi1, list) or len(aoi1) != 2 or None in aoi1:
        raise ValueError("AOI1 incompleta: " + versao + "/" + imgid)

    linhas_codigo = dados.get("linhasCodigo", [])
    linhas_aoi1 = dados.get("linhasAoi1", [])
    aoi2 = dados.get("aoi2")
    if not isinstance(aoi2, list) or len(aoi2) != 2 or None in aoi2:
        aoi2 = [0, 0]

    return codigo, linhas_codigo, aoi1, linhas_aoi1, aoi2


def retornaLimitesDoCodigo(configuracao, versao, imgid, altura_tela):
    """Retorna (xmin, xmax, ymin, ymax) no sistema usado pelos graficos.

    Os limites verticais das AOIs foram medidos a partir do topo da tela,
    enquanto o script inverte o eixo Y dos dados do eye tracker. Por isso os
    limites tambem precisam ser convertidos com ``altura_tela - y``.
    """
    codigo, _, _, _, _ = retornaLimitesDasAOIs(configuracao, versao, imgid)
    topo, base = min(codigo), max(codigo)
    xmin, xmax = 245, 820
    ymin = altura_tela - base
    ymax = altura_tela - topo
    return xmin, xmax, ymin, ymax


def filtraFixacoesDoCodigo(df, limites_codigo):
    """Mantem apenas fixacoes localizadas dentro do painel de codigo."""
    xmin, xmax, ymin, ymax = limites_codigo
    return df.loc[
        df.x.between(xmin, xmax, inclusive="both")
        & df.y.between(ymin, ymax, inclusive="both")
    ].copy()

# ============================================================
# Utilities
# ============================================================
def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

def saveImage(plt,imagem,dpiVal=200):
    plt.savefig(imagem, bbox_inches='tight', dpi=dpiVal)
    plt.clf()

def alteraMargens(ax,iniX,fimX,iniY,fimY):
    ax.set(xlim=(iniX, fimX))
    ax.set(ylim=(iniY, fimY))

def converteTempoParaSegundos(df):
    for i in range(0, len(df.index)):
        string = df.tempo[i]
        lista = string.split(":")
        tempo = int(lista[0])*3600000+int(lista[1])*60000+int(lista[2])*1000+int(lista[3])
        df.loc[i, 'tempo'] = str(int(tempo))
            
    # como o tempo sempre aumenta, vamos focar no tempo relativo ao inicio
    df.tempo = df.tempo.values.astype(np.int64)
    # assumimos que o 1o valor e o menor do tempo. 
    # Dividimos por 1000 para considerarmos em segundos
    df.tempo = (df.tempo - df.tempo[0])/1000    
    return df

#altera os dados de tempo para milisegundos
def converteSegundosParaMilisegundos(df): 
    for i in range(0, len(df.index)):
        tempo = df.tempo[i] * 1000 
        df.loc[i, 'tempo'] = int(tempo)
      
    return df

#salva imagem
def salvaImagem(plt,imagem,dpiVal=200):
    plt.savefig(imagem, bbox_inches='tight', dpi=dpiVal)
    plt.clf()
# =========================
# Gaze points correction
# =========================
def correctPointsYaxis(participante, tarefa):
    dy = 0
    
    if participante == "001":
        dy = 15
    elif participante == "002":
        dy = 30
    elif participante == "032":
        dy = 30

    return dy

# =========================
# Visualization
# =========================
#gera grafico scanpath (eixo X e Y) em funcao do tempo
def geraGraficoEixoYOneColor(df, diretorio, participante, tarefa, x, y, imagem):
       
    map_img = mpimg.imread(imagem)
    #regioes, subregioesaoi, aoi, subregiaoCorreta_1, subregiaoIncorreta_1, subregiaoCorreta_2, subregiaoIncorreta_2 = retornaLimitesDeLinhasIfdefs(tarefa, y)
    limiteInferior = 0
    limiteSuperior = 768
    colorss = []
    
    for i in range(len(df)-1):
        if (df.y[i] > limiteInferior and df.y[i] < limiteSuperior and df.y[i+1] > limiteInferior and df.y[i+1] < limiteSuperior):
            colorss.append('red')
        else:
            colorss.append('grey')

    cmap = ListedColormap(colorss)

    xy = np.array([df.x, df.y]).T.reshape(-1, 1, 2)
    segments = np.hstack([xy[:-1], xy[1:]])

    lc = LineCollection(segments, color = colorss)
    # plot
    fig, ax = plt.subplots()
    ax.add_collection(lc)
    ax.set_title("Participant: "+participante+ " Task: "+tarefa)
    plt.ylabel('Code y-axis (pixels)', fontsize=10)
    plt.xlabel('Code x-axis (pixels)', fontsize=10)

    ax.autoscale()
    fig.set_size_inches(10, 6)
    plt.imshow(map_img, zorder=0, extent=[0.0, x, 0.0, y])
    plt.savefig(diretorio+'one color ('+participante+' '+ tarefa+').png')
    plt.close()

def visualizeFixationsPoints(df, diretorio, participante, tarefa, x, y, imagem):
    plt.close("all")
    map_img = mpimg.imread(imagem)
    ax = sns.scatterplot(x=df.x, y=df.y, size=df.duracao)
    alteraMargens(ax,0,x,0,y)
    
    plt.imshow(map_img, zorder=0, extent=[0.0, x, 0.0, y])
    ax.set_title("Participant: "+participante+ " Task: "+tarefa)
    saveImage(plt,diretorio+'Pontos Fixations ('+participante+' '+ tarefa+').png')

def visitedLinesOrder(regioes, df, part, imgid, diretorio):
    for index, row in df.iterrows():
        temp = row['y']
        detectLineCode(regioes,temp, part, imgid, diretorio)

def detectLineCode(regioes, x, part, imgid, diretorio):
    tam = len(regioes)
    inicio = 0
    while (inicio < tam):
        if(x<regioes[inicio]):
            a = open(diretorio+""+part+" "+imgid+" arestas saccades.txt","a")
            a.write(str(tam-inicio)+' ')
            a.close()
            break
        inicio = inicio+1

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

#gera grafico de pontos com duracao de fixacoes de um participante de uma tarefa especifica
def geraGraficoDePontosFixationTransparenteParaUmPart(
    df, diretorio, participante, tarefa, x, y, imagem, limites_codigo
):
    plt.close("all")
    map_img = mpimg.imread(imagem)
    ax = sns.scatterplot(x=df.x, y=df.y, size=df.duracao, alpha = .4 ,edgecolor='none', color = 'red')
    xmin, xmax, ymin, ymax = limites_codigo
    alteraMargens(ax, xmin, xmax, ymin, ymax)

    # Mantem a imagem nas coordenadas da tela e usa o eixo como janela de
    # recorte. Assim as fixacoes nao sao redimensionadas nem deslocadas.
    plt.imshow(map_img, zorder=0, extent=[0.0, x, 0.0, y])
    ax.set_title("Participant: "+participante+ " Task: "+tarefa)
    salvaImagem(plt,diretorio+'Pontos Fixations Transparent('+participante+' '+ tarefa+').png')


def visualizeScanPath(df, diretorio, participante, tarefa, x, y, imagem):
    map_img = mpimg.imread(imagem)
    limiteInferior = 0
    limiteSuperior = 768
    colorss = []
    for i in range(len(df)-1):
        if (df.y[i] > limiteInferior and df.y[i] < limiteSuperior and df.y[i+1] > limiteInferior and df.y[i+1] < limiteSuperior):
            colorss.append('red')
        else:
            colorss.append('grey')
    cmap = ListedColormap(colorss)
    xy = np.array([df.x, df.y]).T.reshape(-1, 1, 2)
    segments = np.hstack([xy[:-1], xy[1:]])
    lc = LineCollection(segments, color = colorss)
    fig, ax = plt.subplots()
    ax.add_collection(lc)
    ax.set_title("Participant: "+participante+ " Task: "+tarefa)
    plt.ylabel('Code y-axis (pixels)', fontsize=10)
    plt.xlabel('Code x-axis (pixels)', fontsize=10)
    ax.autoscale()
    fig.set_size_inches(10, 6)
    plt.imshow(map_img, zorder=0, extent=[0.0, x, 0.0, y])
    plt.savefig(diretorio+'Scanpath ('+participante+' '+ tarefa+').png')
    plt.close()

#gera mapa de calor baseado nas fixacoes de participantes individuais de uma tarefa especifica
# def geraHeatmapBaseadoEmFixacaoDuracao(imagem, diretorio, dfx, dfy, dfduracao, x, y, participante, tarefa, upperBound):
#     plt.close("all")
#     map_img = mpimg.imread(imagem)
#     xmin, xmax = 0, x
#     ymin, ymax = 0, y
    
#     # Peform the kernel density estimate
#     xx, yy = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
#     positions = np.vstack([xx.ravel(), yy.ravel()])
#     values = np.vstack([dfx, dfy])
#     kernel = st.gaussian_kde(values, weights = dfduracao)
#     f = np.reshape(kernel(positions).T, xx.shape)
    
#     fig = pl.figure()
#     ax = fig.gca()
#     ax.set_xlim(xmin, xmax)
#     ax.set_ylim(ymin, ymax)
#     # Contourf plot
#     cfset = ax.contourf(xx, yy, f, cmap='Reds', levels = 10)
#     ## Or kernel density estimate plot instead of the contourf plot
#     #ax.imshow(np.rot90(f), cmap='Blues', extent=[xmin, xmax, ymin, ymax])
    
#     #alpha = (len(dfx) - 0) / (upperBound - 0)
#     #for i in range(len(cfset.collections)):
#         #colore de acordo com o aplha
#         #cfset.collections[i].set_alpha((i*0.1)*alpha)
    
#     # Contour plot
#     #cset = ax.contour(xx, yy, f, colors='grey', levels = 10)
#     # Label plot
#     #cfset.collections[0].set_alpha(0.0)
#     #ax.clabel(cset, inline=1, fontsize=10)
#     #ax.set_title("Participant: "+participante+ " Task: "+tarefa)

#     alpha = len(dfx) / upperBound
#     alpha = min(max(alpha, 0.0), 1.0)

#     cores = cfset.get_facecolors()

#     for i in range(len(cores)):
#         cores[i, 3] = (i * 0.1) * alpha

#     if len(cores) > 0:
#         cores[0, 3] = 0.0

#     cfset.set_facecolors(cores)

#     ax.set_ylabel("y-coordinate")
#     ax.set_xlabel("x-coordinate")

#     plt.imshow(map_img, zorder=0, extent=[0.0, x, 0.0, y])
#     salvaImagem(plt,diretorio+'Heatmap Fix com Duracao ('+ tarefa+').png')

def geraHeatmapBaseadoEmFixacaoDuracao(
    imagem, diretorio, dfx, dfy, dfduracao, x, y, participante, tarefa,
    upperBound, limites_codigo
):
    plt.close("all")
    map_img = mpimg.imread(imagem)
    xmin, xmax, ymin, ymax = limites_codigo
    
    # Peform the kernel density estimate
    xx, yy = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
    positions = np.vstack([xx.ravel(), yy.ravel()])
    values = np.vstack([dfx, dfy])
    kernel = st.gaussian_kde(values, weights = dfduracao)
    f = np.reshape(kernel(positions).T, xx.shape)
    
    fig = pl.figure()
    ax = fig.gca()
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    # Contourf plot
    #cfset = ax.contourf(xx, yy, f, cmap='Reds', levels = 10)
    ## Or kernel density estimate plot instead of the contourf plot
    #ax.imshow(np.rot90(f), cmap='Blues', extent=[xmin, xmax, ymin, ymax])
    
    #alpha = (len(dfx) - 0) / (upperBound - 0)
    #for i in range(len(cfset.collections)):
        #colore de acordo com o aplha
        #cfset.collections[i].set_alpha((i*0.1)*alpha)
    
    # Contour plot
    #cset = ax.contour(xx, yy, f, colors='grey', levels = 10)
    # Label plot
    #cfset.collections[0].set_alpha(0.0)
    #ax.clabel(cset, inline=1, fontsize=10)
    #ax.set_title("Participant: "+participante+ " Task: "+tarefa)

    # alpha = len(dfx) / upperBound
    # alpha = min(max(alpha, 0.0), 1.0)

    # cores = cfset.get_facecolors()

    # for i in range(len(cores)):
    #     cores[i, 3] = (i * 0.1) * alpha

    # if len(cores) > 0:
    #     cores[0, 3] = 0.0

    # cfset.set_facecolors(cores)

    # Desenha a imagem da tarefa no fundo
    ax.imshow(
        map_img,
        zorder=0,
        extent=[0.0, x, 0.0, y],
        aspect='auto'
    )

    # Transparência baseada na quantidade de fixações
    alpha = len(dfx) / upperBound
    alpha = min(max(alpha, 0.0), 1.0)

    # Cria uma escala vermelha com transparência crescente
    cores = plt.cm.Reds(np.linspace(0, 1, 10))
    cores[:, 3] = np.linspace(0, alpha, 10)

    # O primeiro nível fica completamente transparente
    cores[0, 3] = 0.0

    mapa_cores = ListedColormap(cores)

    # Desenha o heatmap sobre a imagem
    cfset = ax.contourf(
        xx,
        yy,
        f,
        cmap=mapa_cores,
        levels=10,
        zorder=1
    )

    ax.set_ylabel("y-coordinate")
    ax.set_xlabel("x-coordinate")

    #plt.imshow(map_img, zorder=0, extent=[0.0, x, 0.0, y])
    salvaImagem(plt,diretorio+'Heatmap Fix com Duracao ('+ tarefa+').png')

def connectpoints(x,y,p1,p2,cont,inicio):    
    x1, x2 = x.iloc[p1], x.iloc[p2]
    y1, y2 = y.iloc[p1], y.iloc[p2]
    if(cont==-1):
        plt.arrow(x1,y1,x2-x1,y2-y1, head_width=15, head_length=10, fc='r', ec='r',length_includes_head=True)#k
    elif(cont==0):
        plt.arrow(x1,y1,x2-x1,y2-y1, head_width=15, head_length=10, fc='r', ec='r',length_includes_head=True )#r
    elif(cont==1):
        plt.arrow(x1,y1,x2-x1,y2-y1, head_width=15, head_length=10, fc='r', ec='r',length_includes_head=True)#y
    else:  
        plt.arrow(x1,y1,x2-x1,y2-y1, head_width=15, head_length=10, fc='r', ec='r',length_includes_head=True)#b


def addHeaderSepSemicolon(diretorio):
    dfsum = pd.read_csv(diretorio, header=None)
    dfsum.to_csv(diretorio, header=["Participante","Tarefa", "Time_in_Code_Secs", 
                                    "Num_of_Fixations_in_Code", "Dur_of_Fixations_in_Code_secs","Num_of_Regressions_in_Code",
                                    "Num_of_Horizontal_Regressions_in_Code", "Num_of_Vertical_Regressions_in_Code",

                                    "Time_in_AOI1_Secs", "Num_of_Fixations_in_AOI1", "Dur_of_Fixations_in_AOI1","Num_of_Regressions_in_AOI1", 
                                    "Num_of_Horizontal_Regressions_in_AOI1", "Num_of_Vertical_Regressions_in_AOI1",
                                    "Entries_AOI1", "Entries_AOI1_from_top", "Entries_AOI1_from_bottom", "Exits_AOI1_to_top", "Exits_AOI1_to_bottom",

                                     "Time_in_AOI2_Secs", "Num_of_Fixations_in_AOI2", "Dur_of_Fixations_in_AOI2","Num_of_Regressions_in_AOI2", 
                                    "Num_of_Horizontal_Regressions_in_AOI2", "Num_of_Vertical_Regressions_in_AOI2",
                                    "Entries_AOI2", "Entries_AOI2_from_top", "Entries_AOI2_from_bottom", "Exits_AOI2_to_top", "Exits_AOI2_to_bottom"
                                    ], sep=";", index=False)

# ============================================================
# Main experiment loop for all subjects and tasks
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Gera graficos usando a ordem real registrada pelo experimento."
    )
    parser.add_argument("--participant", default="P00")
    parser.add_argument(
        "--data-dir",
        default="C:/Users/EASY acadêmico/Documents/demo/data"
    )
    parser.add_argument(
        "--images-dir",
        default="C:/Users/EASY acadêmico/Documents/demo/telas"
    )
    parser.add_argument(
        "--graphs-dir",
        default="C:/Users/EASY acadêmico/Documents/demo/graficos"
    )
    parser.add_argument(
        "--mapping",
        help="ordem_tarefas.csv; por padrao fica na pasta de dados do participante"
    )
    parser.add_argument(
        "--aoi-config",
        default=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "aoi_por_versao.json"
        )
    )
    args = parser.parse_args()
    configuracao_aoi = carregaConfiguracaoDasAOIs(args.aoi_config)

    participante = args.participant
    if not participante.startswith("P"):
        participante = "P" + participante

    pasta_dados = os.path.join(args.data_dir, participante)
    mapping_path = args.mapping or os.path.join(pasta_dados, "ordem_tarefas.csv")
    ordem = pd.read_csv(mapping_path)

    colunas_necessarias = {
        "Arquivo", "TarefaReal", "PosicaoExecucao", "VersaoExperimento"
    }
    colunas_ausentes = colunas_necessarias.difference(ordem.columns)
    if colunas_ausentes:
        raise ValueError(
            "Colunas ausentes em ordem_tarefas.csv: "
            + ", ".join(sorted(colunas_ausentes))
        )
    if "Participante" in ordem.columns:
        participantes_mapeados = set(ordem.Participante.astype(str))
        if participantes_mapeados != {participante}:
            raise ValueError(
                "O participante do mapeamento nao corresponde a " + participante
            )

    ordem = ordem.sort_values("PosicaoExecucao")
    if len(ordem) != 6 or ordem.TarefaReal.nunique() != 6:
        raise ValueError("ordem_tarefas.csv deve mapear seis tarefas diferentes")
    versoes = set(ordem.VersaoExperimento.astype(str).str.lower())
    if len(versoes) != 1 or not versoes.issubset({"lambda", "omega"}):
        raise ValueError("A versao do experimento deve ser somente lambda ou omega")

    for _, item_ordem in ordem.iterrows():
            tarefa = str(item_ordem.TarefaReal)
            versao = str(item_ordem.VersaoExperimento).lower()
            arquivo_posicao = str(item_ordem.Arquivo)
            print(participante)
            dados_dir = os.path.join(pasta_dados, arquivo_posicao)
            imagem = os.path.join(args.images_dir, versao, tarefa + ".png")
            if not os.path.isfile(imagem):
                raise FileNotFoundError("Tela nao encontrada: " + imagem)
            df = pd.read_csv(dados_dir)

            x = 1920
            y = 1080     

            diretorio = os.path.join(
                args.graphs_dir, participante, participante + tarefa
            ) + os.sep
            createFolder(diretorio)

            dy = correctPointsYaxis(participante, tarefa)
            dx = 0
            
            converteTempoParaSegundos(df)
            df = converteSegundosParaMilisegundos(df)
            
            # serve para colocar o eixo (0,0) no canto superior esquerdo da tela
            df.y = y-df.y
            df.y = df.y + dy
            df.x = df.x + dx
            

            #computa fixations
            Sfix, Efix = fixation_detection(df.x, df.y, df.tempo)
            
            fixation_path = os.path.join(
                pasta_dados, "Fixations " + participante + " " + tarefa + ".csv"
            )
            with open(fixation_path, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["tempo", "tempofinal", "duracao","x", "y"])
                for i in Efix:
                     writer.writerow(i)
            dffixation = pd.read_csv(fixation_path)
            
            codigo, linhas_codigo, aoi1, linhas_aoi1, aoi2 = retornaLimitesDasAOIs(
                configuracao_aoi, versao, tarefa
            )
            limites_codigo = retornaLimitesDoCodigo(
                configuracao_aoi, versao, tarefa, y
            )
            dffixation_codigo = filtraFixacoesDoCodigo(
                dffixation, limites_codigo
            )
            print(
                "Recorte do codigo " + tarefa + ": "
                + "x={0}..{1}, y={2}..{3}; fixacoes={4}/{5}".format(
                    *limites_codigo,
                    len(dffixation_codigo),
                    len(dffixation)
                )
            )
            
            limite_inferior_codigo = codigo[0]
            limite_superior_codigo = codigo[1]

            limite_inferior_aoi1 = aoi1[0]
            limite_superior_aoi1 = aoi1[1]

            limite_inferior_aoi2 = aoi2[0]
            limite_superior_aoi2 = aoi2[1]

            print(participante)
            print(tarefa)
            
            # geraGraficoEixoYOneColor(dffixation, diretorio, participante, tarefa, x, y, imagem)
            geraGraficoDePontosFixationTransparenteParaUmPart(
                dffixation_codigo, diretorio, participante, tarefa,
                x, y, imagem, limites_codigo
            )
            if len(dffixation_codigo) >= 2:
                geraHeatmapBaseadoEmFixacaoDuracao(
                    imagem, diretorio, dffixation_codigo.x,
                    dffixation_codigo.y, dffixation_codigo.duracao,
                    x, y, participante, tarefa, 200, limites_codigo
                )
            else:
                print(
                    "Heatmap ignorado: menos de duas fixacoes "
                    "na area do codigo"
                )
                
# ============================================================
# Execution
# ============================================================
if __name__ == "__main__":
    main()

