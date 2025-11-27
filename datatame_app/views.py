from django.shortcuts import render, redirect, get_object_or_404
#from .forms import AtletaSignupForm
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from .models import AnaliseAtleta, Equipe, LutaRegistrada, Atleta,User, Perfil
from .forms import LutaRegistradaForm
import sqlite3
from django.conf import settings
from .decorators import session_required
from datatame_app.machine_learning_datatame.ml_adapter import gerar_analise_atleta
from django.core.paginator import Paginator


def logout_view(request):
    request.session.flush() 
    return redirect('login')  

def home(request):
    user_id = request.session.get("user_id")
    tipo = request.session.get("tipo")
    user = None
    if user_id:
        from .models import User
        user = User.objects.get(id=user_id)
    return render(request, "home.html", {"user_custom": user})

def login(request):
    erro = None

    if request.method == "POST":
        email = request.POST.get("email")
        senha = request.POST.get("senha")
        print("Email recebido:", email)
        print("Senha recebida:", senha)

        try:
            user = User.objects.get(email=email)
            print("Usuário encontrado:", user)

            if user.check_senha(senha):
                print("Senha correta")
                request.session["user_id"] = user.id
                request.session["tipo"] = user.tipo
                
            
                if user.tipo == "atleta":
                    return redirect("dashboard_atleta")
                elif user.tipo == "equipe":
                    return redirect("dashboard_equipe")
                else:
                    return redirect("home") 
                    
            else:
                print("Senha incorreta")
                erro = "Senha incorreta."
        except User.DoesNotExist:
            print("Email não encontrado")
            erro = "Email não encontrado."

    return render(request, "login.html", {"erro": erro})

def signup_atleta(request):
    if request.method == "POST":
        email = request.POST["email"]
        senha = request.POST.get("password")

        # Evitar email duplicado
        if User.objects.filter(email=email).exists():
            equipes = Equipe.objects.all()
            return render(request, "signup_atleta.html", {
                "equipes": equipes,
                "error": "Este email já está cadastrado."
            })

        # Criar o User
        user = User(email=email, tipo="atleta")
        user.set_senha(senha)
        user.save(force_insert=True)

        # Criar o Atleta
        atleta = Atleta.objects.create(
            usuario=user,
            nome=request.POST["nome"],
            idade=request.POST["idade"],
            categoria_peso=request.POST["categoria_peso"],
            sexo=request.POST["sexo"],
            equipe_id=request.POST.get("equipe")
        )

        # Criar perfil
        Perfil.objects.create(
            user=user,
            tipo="ATLETA",
            atleta=atleta
        )

        # salvar ID na sessão
        request.session["user_id"] = user.id

        return redirect("login")

    equipes = Equipe.objects.all()
    return render(request, "signup_atleta.html", {"equipes": equipes})

def signup_equipe(request):
    if request.method == "POST":
        email = request.POST["email"]
        senha = request.POST.get("password")

        # Criar o User
        user = User(email=email, tipo="equipe")
        user.set_senha(senha)
        user.save()

        # Criar o perfil Equipe
        equipe = Equipe.objects.create(
            usuario=user,
            nome=request.POST["nome_equipe"],
            quantidade_atletas=request.POST["quantidade_atletas"],
            cidade=request.POST["cidade"],
            estado=request.POST["estado"]
        )

        Perfil.objects.create(
            user=user,
            tipo="EQUIPE",
            equipe=equipe
        )

        return redirect("login")

    return render(request, "signup_equipe.html")

def signup_escolha(request):
    return render(request, "signup_escolha.html")

@session_required
def registrar_luta(request):

    user_id = request.session.get("user_id")
    user = User.objects.get(id=user_id)

    perfil = Perfil.objects.filter(user=user).first()
    if not perfil:
        return HttpResponse("Erro: perfil não encontrado para esse usuário.")

    if perfil.tipo != "EQUIPE":
        return HttpResponse("Apenas equipes podem registrar lutas.")

    equipe = perfil.equipe

    atletas = Atleta.objects.filter(equipe=equipe)

    if request.method == 'POST':
        form = LutaRegistradaForm(request.POST, equipe=equipe)
        form.fields['atleta'].queryset = atletas

        if form.is_valid():
            luta = form.save()
            messages.success(request, "Luta registrada com sucesso!")
            return redirect("dashboard_equipe")

    else:
        form = LutaRegistradaForm(equipe=equipe)
        form.fields['atleta'].queryset = atletas

    return render(request, "registrar_luta.html", {"form": form})

@session_required
def dashboard_equipe(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(id=user_id)
    perfil = Perfil.objects.filter(user=user).first()
    equipe = perfil.equipe
    atletas = Atleta.objects.filter(equipe=equipe)
    total_lutas = LutaRegistrada.objects.filter(atleta__in=atletas).count()

    for atleta in atletas:
        atleta.vitorias = LutaRegistrada.objects.filter(atleta=atleta, resultado="1").count()
        atleta.derrotas = LutaRegistrada.objects.filter(atleta=atleta, resultado="0").count()

    # ---- Buscar total de lutas no ML ----
    ml_path = settings.BASE_DIR / 'datatame_app' / 'machine_learning_datatame' / 'lutas.db'
    conn = sqlite3.connect(str(ml_path))
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM lutas")


    return render(request, "dashboard.html", {
        "equipe": equipe,
        "atletas": atletas,
        "total_lutas": total_lutas, 
    })



@session_required
def registrar_luta(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(id=user_id)
    perfil = Perfil.objects.filter(user=user).first()
    equipe = perfil.equipe

    atletas = Atleta.objects.filter(equipe=equipe)

    if request.method == "POST":
        form = LutaRegistradaForm(request.POST)
        form.fields["atleta"].queryset = atletas

        if form.is_valid():
            luta = form.save()  # salva no Django
            luta.enviar_para_ml_db()

            ippon_dif = luta.ippon_atl - luta.ippon_op
            wazari_dif = luta.wazari_atl - luta.wazari_op
            yuko_dif = luta.yuko_atl - luta.yuko_op

            newaza_tent_dif = luta.newaza_tentativas_atl - luta.newaza_tentativas_op
            newaza_acert_dif = luta.newaza_acertos_atl - luta.newaza_acertos_op

            tewaza_tent_dif = luta.tewaza_tentativas_atl - luta.tewaza_tentativas_op
            tewaza_acert_dif = luta.tewaza_acertos_atl - luta.tewaza_acertos_op

            koshi_tent_dif = luta.koshiwaza_tentativas_atl - luta.koshiwaza_tentativas_op
            koshi_acert_dif = luta.koshiwaza_acertos_atl - luta.koshiwaza_acertos_op

            ashi_tent_dif = luta.ashiwaza_tentativas_atl - luta.ashiwaza_tentativas_op
            ashi_acert_dif = luta.ashiwaza_acertos_atl - luta.ashiwaza_acertos_op

            sutemi_tent_dif = luta.sutemiwaza_tentativas_atl - luta.sutemiwaza_tentativas_op
            sutemi_acert_dif = luta.sutemiwaza_acertos_atl - luta.sutemiwaza_acertos_op

            iniciativa_dif = luta.iniciativa_pegada_atl - luta.iniciativa_pegada_op

            # resultado em int
            resultado_int = 1 if luta.resultado == "vitoria" else 0

          
            return redirect("dashboard_equipe")
        else:
             print("ERROS:", form.errors)    
    else:
        form = LutaRegistradaForm()
        form.fields["atleta"].queryset = atletas
        print("ERROS:", form.errors)
    return render(request, "registrar_luta.html", {"form": form})

def detalhes_atleta(request, pk):
    atleta = get_object_or_404(Atleta, pk=pk)
    return render(request, 'detalhes_atleta.html', {'atleta': atleta})

def listar_lutas(request):
    user_id = request.session.get("user_id")
    user = User.objects.get(id=user_id)
    perfil = Perfil.objects.filter(user=user).first()
    equipe = perfil.equipe

    lutas = LutaRegistrada.objects.filter(atleta__equipe=equipe)
    atleta_nome = request.GET.get('atleta')
    resultado_filter = request.GET.get('resultado')

    if atleta_nome:
        lutas = lutas.filter(atleta__nome__icontains=atleta_nome)

    if resultado_filter in ['0', '1']:  # só aceita 0 ou 1
        lutas = lutas.filter(resultado=(resultado_filter == '1'))

    paginator = Paginator(lutas, 24)
    page_number = request.GET.get('page')
    lutas = paginator.get_page(page_number)
    return render(request, "listar_lutas.html", {
        "lutas": lutas,
        "equipe": equipe
    })



def analise_atleta(request, nome,):
    ml_path = settings.BASE_DIR / 'datatame_app' / 'machine_learning_datatame' / 'lutas.db'
    resultados = gerar_analise_atleta(nome, db_path=str(ml_path))
    atleta = get_object_or_404(Atleta, nome=nome)
    lutas_list  = LutaRegistrada.objects.filter(atleta=atleta).order_by("-criado_em")
    paginator = Paginator(lutas_list , 4) 
    page_number = request.GET.get('page')
    lutas = paginator.get_page(page_number)

    return render(request, "analise_resultado.html", {
       "atleta": atleta,
        "lutas": lutas,
        "resultados": resultados,
    })
@session_required
def dashboard_atleta(request):
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")

    # Buscar o usuário autenticado
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect("login")

    # Garantir que é atleta
    if user.tipo != "atleta":
        return redirect("dashboard_equipe")

    # Obter o atleta vinculado
    atleta = Atleta.objects.filter(usuario=user).first()
    if not atleta:
        return HttpResponse("Erro: atleta não encontrado.")

    # Obter lutas
    lutas_list = LutaRegistrada.objects.filter(atleta=atleta).order_by("-criado_em")
    paginator = Paginator(lutas_list, 5)  # 5 por página
    page_number = request.GET.get("page")
    lutas = paginator.get_page(page_number)

    # Totais
    total_lutas = lutas_list.count()
    total_vitorias = lutas_list.filter(resultado=True).count()
    total_derrotas = lutas_list.filter(resultado=False).count()

    # Resultados ML
    ml_path = settings.BASE_DIR / "datatame_app" / "machine_learning_datatame" / "lutas.db"
    resultados_ml = gerar_analise_atleta(atleta.nome, db_path=str(ml_path))

    return render(request, "dashboard_atleta.html", {
        "atleta": atleta,
        "lutas": lutas,
        "total_lutas": total_lutas,
        "total_vitorias": total_vitorias,
        "total_derrotas": total_derrotas,
        "resultados_ml": resultados_ml,
    })


def detalhe_luta(request, luta_id):
    luta = get_object_or_404(LutaRegistrada, id=luta_id)
    estatisticas_atleta = [
        ("Ashi Waza", luta.ashiwaza_tentativas_atl, luta.ashiwaza_acertos_atl),
        ("Koshi Waza", luta.koshiwaza_tentativas_atl, luta.koshiwaza_acertos_atl),
        ("Tewaza", luta.tewaza_tentativas_atl, luta.tewaza_acertos_atl),
        ("Sutemi Waza", luta.sutemiwaza_tentativas_atl, luta.sutemiwaza_acertos_atl),
        ("Newaza", luta.newaza_tentativas_atl, luta.newaza_acertos_atl),
        ("Wazari", None, luta.wazari_atl),
        ("Yuko", None, luta.yuko_atl),
        ("Ippon", None, luta.ippon_atl),
        ("Shidos", None, luta.shidos_atleta),
    ]

    # Estatísticas do adversário (tentativas/acertos)
    estatisticas_oponente = [
        ("Ashi Waza", luta.ashiwaza_tentativas_op, luta.ashiwaza_acertos_op),
        ("Koshi Waza", luta.koshiwaza_tentativas_op, luta.koshiwaza_acertos_op),
        ("Tewaza", luta.tewaza_tentativas_op, luta.tewaza_acertos_op),
        ("Sutemi Waza", luta.sutemiwaza_tentativas_op, luta.sutemiwaza_acertos_op),
        ("Newaza", luta.newaza_tentativas_op, luta.newaza_acertos_op),
        ("Wazari", None, luta.wazari_op),
        ("Yuko", None, luta.yuko_op),
        ("Ippon", None, luta.ippon_op),
        ("Shidos", None, luta.shidos_oponente),
    ]
    return render(request, "detalhe_luta.html", {
        "estatisticas_atleta": estatisticas_atleta,
        "estatisticas_oponente": estatisticas_oponente,
        "luta": luta
    })
