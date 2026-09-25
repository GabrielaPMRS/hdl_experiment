import csv
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from fontes_agregados import seleciona_fontes

class FontesTest(unittest.TestCase):
    def cria(self, root, nome):
        pasta = root / nome
        pasta.mkdir(parents=True)
        versao = 'lambda' if int(nome[1:]) % 2 == 0 else 'omega'
        with (pasta/'resumo_tarefas.csv').open('w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Participante','TarefaReal','PosicaoExecucao','VersaoExperimento'])
            for i, tarefa in enumerate(('T01','T02','T04','T05'),1):
                writer.writerow([nome,tarefa,i,versao])
                (pasta/f'Fixations {nome} {tarefa}.csv').write_text('x,y,duracao\n300,600,250\n')
        return pasta
    def test_preferencia_e_unicidade(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.cria(root/'data','P00')
            recuperada = self.cria(root/'recuperados/data','P00')
            self.cria(root/'data','P01')
            fontes = seleciona_fontes(root/'data')
            self.assertEqual(len(fontes),2)
            self.assertEqual(fontes[0][0],recuperada.resolve())
    def test_nao_usa_antigo_se_recuperado_ausente(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.cria(root/'data','P00')
            with self.assertRaises(FileNotFoundError): seleciona_fontes(root/'data')
    def test_recuperado_incompleto(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.cria(root/'data','P00')
            pasta=self.cria(root/'recuperados/data','P00')
            (pasta/'Fixations P00 T05.csv').unlink()
            with self.assertRaises(FileNotFoundError): seleciona_fontes(root/'data')
    def test_recuperado_sem_pasta_normal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            pasta=self.cria(root/'recuperados/data','P03')
            self.assertEqual(seleciona_fontes(root/'data'),[(pasta.resolve(),'omega')])

if __name__ == '__main__': unittest.main()
