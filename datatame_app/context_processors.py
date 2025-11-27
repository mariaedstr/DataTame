from .models import User, Atleta, Equipe

def custom_user(request):
    user_custom = None
    nome = None
    user_id = request.session.get("user_id")
    if user_id:
        try:
            user_custom = User.objects.get(id=user_id)
            # Pega o nome dependendo do tipo
            if user_custom.tipo == "atleta":
                atleta = Atleta.objects.filter(usuario=user_custom).first()
                if atleta:
                    nome = atleta.nome
            elif user_custom.tipo == "equipe":
                equipe = Equipe.objects.filter(usuario=user_custom).first()
                if equipe:
                    nome = equipe.nome
        except User.DoesNotExist:
            pass
    return {
        "user_custom": user_custom,
        "user_nome": nome,
        "is_authenticated": user_custom is not None
    }
