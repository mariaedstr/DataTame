from django.contrib import admin
from .models import Atleta, Desempenho, Treino, Equipe,LutaRegistrada


admin.site.register(Atleta)
admin.site.register(Desempenho)
admin.site.register(Treino)
admin.site.register(Equipe)
admin.site.register(LutaRegistrada)
