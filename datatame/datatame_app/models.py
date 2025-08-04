from django.db import models

class Atleta(models.Model):
    nome = models.CharField(max_length=100)
    idade = models.IntegerField()
    categoria_peso = models.CharField(max_length=50)
    sexo = models.CharField(max_length=10)
    equipe = models.CharField(max_length=100) 

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
