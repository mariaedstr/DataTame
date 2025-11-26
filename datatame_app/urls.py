from django.urls import path
from .views import home, login, logout_view, signup_equipe,signup_escolha, analise_atleta, signup_atleta, registrar_luta
from .views import dashboard_equipe, registrar_luta, detalhes_atleta, listar_lutas, dashboard_atleta, detalhe_luta
urlpatterns = [
    path("", home, name="home"),
    path('login/', login, name='login'),
    path('logout/', logout_view, name='logout'),
    path('signup_atleta/', signup_atleta, name='signup_atleta'),
    path('signup_escolha/', signup_escolha, name='signup_escolha'),
    path('signup_equipe/', signup_equipe, name='signup_equipe'),
    path("analise/<str:nome>/", analise_atleta, name="analise_atleta"),
    path('registrar_luta/', registrar_luta,name='registrar_luta'),
    path("dashboard/", dashboard_equipe, name="dashboard_equipe"),
    path("atleta/<int:pk>/", detalhes_atleta, name="detalhes_atleta"),
    path("lutas/", listar_lutas, name="listar_lutas"),
    path("dashboard_atleta/", dashboard_atleta, name="dashboard_atleta"),
    path("luta/<int:luta_id>/", detalhe_luta, name="detalhe_luta"),

]
