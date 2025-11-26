from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.utils import timezone
 
class User(models.Model):
    email = models.EmailField(unique=True)
    senha = models.CharField(max_length=128)
    tipo = models.CharField(max_length=20)  # "atleta" ou "equipe"

    def set_senha(self, raw_password):
        self.senha = make_password(raw_password)

    def check_senha(self, raw_password):
        return check_password(raw_password, self.senha)

    def __str__(self):
        return self.email

class Perfil(models.Model):
    TIPO_USUARIO = (
        ('ATLETA', 'Atleta'),
        ('EQUIPE', 'Equipe'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPO_USUARIO)

    atleta = models.ForeignKey('Atleta', null=True, blank=True, on_delete=models.SET_NULL)
    equipe = models.ForeignKey('Equipe', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.user.email} ({self.tipo})"



class Equipe(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    quantidade_atletas = models.IntegerField()
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=50)
    
    def __str__(self):
        return self.nome

class Atleta(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=100)
    idade = models.IntegerField()
    categoria_peso = models.CharField(max_length=50)
    sexo = models.CharField(max_length=10)
    equipe = models.ForeignKey(Equipe, on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.nome


class Desempenho(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='desempenhos')
    data_competicao = models.DateField()
    vitorias = models.IntegerField(default=0)
    derrotas = models.IntegerField(default=0)
    ippons = models.IntegerField(default=0)
    wazaris = models.IntegerField(default=0)
    penalidades = models.IntegerField(default=0)
    equipe = models.CharField(max_length=100) 

    def __str__(self):
        return f"{self.atleta.nome} - {self.data_competicao}"


class Treino(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='treinos')
    data_treino = models.DateField()
    tipo_treino = models.CharField(max_length=100)
    duracao_minutos = models.IntegerField()
    intensidade = models.IntegerField()
    equipe = models.CharField(max_length=100) 
    def __str__(self):
        return f"{self.atleta.nome} - {self.data_treino}"
 

class AnaliseAtleta(models.Model):
    atleta = models.CharField(max_length=200)
    dependencia_chave = models.CharField(max_length=200)
    ponto_menos_decisivo = models.CharField(max_length=200)
    estilo = models.CharField(max_length=200)

class Luta(models.Model):
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE)

    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE)
    adversario = models.CharField(max_length=100)

    golpes_atleta = models.IntegerField()
    golpes_adversario = models.IntegerField()

    vantagem_atleta = models.IntegerField(default=0)
    vantagem_adversario = models.IntegerField(default=0)

    penalidade_atleta = models.IntegerField(default=0)
    penalidade_adversario = models.IntegerField(default=0)

    resultado = models.CharField(max_length=20)

    data_registro = models.DateTimeField(auto_now_add=True)

    diferenca_golpes = models.IntegerField(default=0)


    def __str__(self):
        return f"Luta de {self.atleta.nome} ({self.equipe.nome})"
        
class LutaRegistrada(models.Model):
    """Tabela principal do sistema: guarda os dados crus que o usuário
    preenche.
    Depois do save() serão calculadas as diferenças e enviadas ao lutas.db
    para o ML.
    """
    atleta = models.ForeignKey('Atleta', on_delete=models.CASCADE,related_name='lutas')
    adversario = models.CharField(max_length=255, blank=True, null=True)
    tempo_luta_segundos = models.IntegerField(null=True, blank=True)
    shidos_atleta = models.IntegerField(default=0)
    shidos_oponente = models.IntegerField(default=0)
    numero_pausas = models.IntegerField(default=0)
    ippon_atl = models.IntegerField(default=0)
    ippon_op = models.IntegerField(default=0)
    wazari_atl = models.IntegerField(default=0)
    wazari_op = models.IntegerField(default=0)
    yuko_atl = models.IntegerField(default=0)
    yuko_op = models.IntegerField(default=0)
    # Tentativas e acertos por tipo (atleta / adversário)
    newaza_tentativas_atl = models.IntegerField(default=0)
    newaza_tentativas_op = models.IntegerField(default=0)
    newaza_acertos_atl = models.IntegerField(default=0)
    newaza_acertos_op = models.IntegerField(default=0)
    tewaza_tentativas_atl = models.IntegerField(default=0)
    tewaza_tentativas_op = models.IntegerField(default=0)
    tewaza_acertos_atl = models.IntegerField(default=0)
    tewaza_acertos_op = models.IntegerField(default=0)
    koshiwaza_tentativas_atl = models.IntegerField(default=0)
    koshiwaza_tentativas_op = models.IntegerField(default=0)
    koshiwaza_acertos_atl = models.IntegerField(default=0)
    koshiwaza_acertos_op = models.IntegerField(default=0)
    ashiwaza_tentativas_atl = models.IntegerField(default=0)
    ashiwaza_tentativas_op = models.IntegerField(default=0)
    ashiwaza_acertos_atl = models.IntegerField(default=0)
    ashiwaza_acertos_op = models.IntegerField(default=0)
    sutemiwaza_tentativas_atl = models.IntegerField(default=0)
    sutemiwaza_tentativas_op = models.IntegerField(default=0)
    sutemiwaza_acertos_atl = models.IntegerField(default=0)
    sutemiwaza_acertos_op = models.IntegerField(default=0)
    iniciativa_pegada_atl = models.IntegerField(default=0)
    iniciativa_pegada_op = models.IntegerField(default=0)
    # Resultado: 1 vitória do atleta, 0 derrota
    resultado = models.IntegerField(choices=[(1,'Vitória'),(0,'Derrota')],default=0)
    criado_em = models.DateTimeField(default=timezone.now)
    class Meta:
        verbose_name = 'Luta registrada'
        verbose_name_plural = 'Lutas registradas'
        ordering = ['-criado_em']
    def __str__(self):
        return f"{self.atleta.nome} x {self.adversario} - {'V' if self.resultado else 'D'}"
    def calcular_diferencas(self):
        return {
        'atleta': str(self.atleta.nome),
        'tempo_luta_segundos': int(self.tempo_luta_segundos or 0),
        'shidos_atleta': int(self.shidos_atleta or 0),
        'numero_pausas': int(self.numero_pausas or 0),
        'ippon_diferenca': int((self.ippon_atl or 0) - (self.ippon_op or 0)),
        'wazari_diferenca': int((self.wazari_atl or 0) - (self.wazari_op or 0)),
        'yuko_diferenca': int((self.yuko_atl or 0) - (self.yuko_op or 0)),

        'newaza_tentativas_diferenca': int((self.newaza_tentativas_atl or 0) - (self.newaza_tentativas_op or 0)),
        'newaza_acertos_diferenca': int((self.newaza_acertos_atl or 0) - (self.newaza_acertos_op or 0)),
        'tewaza_tentativas_diferenca': int((self.tewaza_tentativas_atl or 0) - (self.tewaza_tentativas_op or 0)),
        'tewaza_acertos_diferenca': int((self.tewaza_acertos_atl or 0) -(self.tewaza_acertos_op or 0)),
        'koshiwaza_tentativas_diferenca': int((self.koshiwaza_tentativas_atl or 0) - (self.koshiwaza_tentativas_op or 0)),
        'koshiwaza_acertos_diferenca': int((self.koshiwaza_acertos_atl or 0) - (self.koshiwaza_acertos_op or 0)),
        'ashiwaza_tentativas_diferenca': int((self.ashiwaza_tentativas_atl or 0) - (self.ashiwaza_tentativas_op or 0)),
        'ashiwaza_acertos_diferenca': int((self.ashiwaza_acertos_atl or 0) - (self.ashiwaza_acertos_op or 0)),
        'sutemiwaza_tentativas_diferenca': int((self.sutemiwaza_tentativas_atl or 0) - (self.sutemiwaza_tentativas_op or 0)),
        'sutemiwaza_acertos_diferenca': int((self.sutemiwaza_acertos_atl or 0) - (self.sutemiwaza_acertos_op or 0)),
        'iniciativa_pegada_diferenca': int((self.iniciativa_pegada_atl or 0) - (self.iniciativa_pegada_op or 0)),
        'resultado': int(self.resultado or 0), }

    def enviar_para_ml_db(self):
        import sqlite3
        from pathlib import Path
        ml_path = settings.BASE_DIR / 'datatame_app' / 'machine_learning_datatame' / 'lutas.db'
        payload = self.calcular_diferencas()
        # Campos existentes na sua tabela ML (ordem não importa, usamos named insert)
        cols = [
            'atleta', 'tempo_luta_segundos', 'shidos_atleta',
            'numero_pausas', 'iniciativa_pegada_diferenca',
            'ippon_diferenca','wazari_diferenca','yuko_diferenca',
            'newaza_tentativas_diferenca', 'newaza_acertos_diferenca',
            'tewaza_tentativas_diferenca', 'tewaza_acertos_diferenca',
            'koshiwaza_tentativas_diferenca', 'koshiwaza_acertos_diferenca',
            'ashiwaza_tentativas_diferenca', 'ashiwaza_acertos_diferenca',
            'sutemiwaza_tentativas_diferenca',
            'sutemiwaza_acertos_diferenca',
            'resultado'
            ]
        values = [payload.get(c, 0) for c in cols]
        conn = sqlite3.connect(str(ml_path))
        cur = conn.cursor()
        # Monta SQL dinâmico seguro
        placeholders = ','.join('?' for _ in cols)
        cols_sql = ','.join(cols)
        sql = f"INSERT INTO lutas ({cols_sql}) VALUES ({placeholders})"
        cur.execute(sql, values)
        conn.commit()
        conn.close()
     