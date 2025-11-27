# datatame_app/ml_adapter.py
import pandas as pd
import sqlite3
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import  accuracy_score


# Coloque aqui o path relativo/nome da tabela padrão se quiser
DEFAULT_TABLE = "lutas"

# Nome amigável das colunas (opcional)
NOMES = {
    'newaza_tentativas_diferenca': 'TÉCNICAS NO SOLO (NE-WAZA)',
    'tewaza_tentativas_diferenca': 'TÉCNICAS DE BRAÇO (TE-WAZA)',
    'koshiwaza_tentativas_diferenca': 'TÉCNICAS DE QUADRIL (KOSHI-WAZA)',
    'ashiwaza_tentativas_diferenca': 'TÉCNICAS DE PERNA (ASHI-WAZA)',
    'sutemiwaza_tentativas_diferenca': 'TÉCNICAS DE SACRIFÍCIO (SUTEMI-WAZA)',
    'iniciativa_pegada_diferenca': 'DOMÍNIO DE PEGADA (KUMI-KATA)',
    'tempo_luta_segundos': 'CONTROLE DE TEMPO',
    'shidos_atleta': 'DISCIPLINA TÁTICA (SHIDO)',
    'numero_pausas': 'GESTÃO DE RITMO (PAUSAS)',
}


def carregar_df(db_path, table_name=DEFAULT_TABLE):
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    finally:
        conn.close()
    return df

def gerar_analise_atleta(atleta_nome, db_path, table_name=DEFAULT_TABLE):
    """
    Retorna dict com informações formatadas para front:
      - dependencia_chave (antiga): nome simples
      - ponto_menos_decisivo (antiga)
      - estilo_atleta (antiga)
      - importancia (dict) (antiga)
      - arma_principal: { 'nome': ..., 'titulo': 'É definido por:', 'analise': '...' }
      - ponto_fraco: { 'nome': ..., 'titulo': 'O atleta deixa a desejar em:', 'conclusao': '...' }
      - classificacao_final: { 'nome': ..., 'descricao': '...' }
    """

    df = carregar_df(db_path, table_name)
    if df is None or df.empty:
        return {
            "dependencia_chave": "Sem dados",
            "ponto_menos_decisivo": "Sem dados",
            "estilo_atleta": "Sem dados",
            "importancia": {},
            "arma_principal": {"nome": "Sem dados", "titulo": "É definido por:", "analise": "Sem dados"},
            "ponto_fraco": {"nome": "Sem dados", "titulo": "O atleta deixa a desejar em:", "conclusao": "Sem dados"},
            "classificacao_final": {"nome": "Sem dados", "descricao": "Sem dados"},
            "acuracia": acuracia,
        }

    atleta = str(atleta_nome)
    df_atl = df[df['atleta'] == atleta].copy()
    df_outros = df[df['atleta'] != atleta].copy()

    features = [
        'tempo_luta_segundos',
        'shidos_atleta',
        'numero_pausas',
        'iniciativa_pegada_diferenca',
        'newaza_tentativas_diferenca',
        'tewaza_tentativas_diferenca',
        'koshiwaza_tentativas_diferenca',
        'ashiwaza_tentativas_diferenca',
        'sutemiwaza_tentativas_diferenca'
    ]

    # proteção contra dados insuficientes
    if len(df_atl) < 5 or len(df_outros) < 5:
        return {
            "dependencia_chave": "Sem dados",
            "ponto_menos_decisivo": "Sem dados",
            "estilo_atleta": "Sem dados",
            "importancia": {},
            "arma_principal": {"nome": "Sem dados", "titulo": "É definido por:", "analise": "Sem dados"},
            "ponto_fraco": {"nome": "Sem dados", "titulo": "O atleta deixa a desejar em:", "conclusao": "Sem dados"},
            "classificacao_final": {"nome": "Sem dados", "descricao": "Sem dados"},
            "acuracia": acuracia,
        }

    # --- calcula importâncias (mantendo a lógica original) ---
    try:
        X_atl = df_atl[features].fillna(0)
        y_atl = df_atl['resultado'].astype(int)

        if y_atl.nunique() < 2:
            X_comb = pd.concat([df_atl[features], df_outros[features]]).fillna(0)
            y_comb = pd.concat([df_atl['resultado'].astype(int), df_outros['resultado'].astype(int)])
            modelo = RandomForestClassifier(n_estimators=100, random_state=42)
            modelo.fit(X_comb, y_comb)
        else:
            modelo = RandomForestClassifier(n_estimators=100, random_state=42)
            modelo.fit(X_atl, y_atl)
        
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X_atl, y_atl, test_size=0.3, random_state=42
            )
            modelo_acuracia = RandomForestClassifier(n_estimators=100, random_state=42)
            modelo_acuracia.fit(X_train, y_train)
            pred = modelo_acuracia.predict(X_test)
            acuracia = round(accuracy_score(y_test, pred) * 100, 2)
        except Exception:
            acuracia = None
        importancias = pd.Series(modelo.feature_importances_, index=features).sort_values(ascending=False)
    except Exception:
        importancias = pd.Series(0, index=features)

    dependencia = importancias.index[0] if not importancias.empty else None
    dependencia_nome = NOMES.get(dependencia, dependencia) if dependencia else "Sem dados"

    ponto_menos = importancias.index[-1] if not importancias.empty else None
    ponto_menos_nome = NOMES.get(ponto_menos, ponto_menos) if ponto_menos else "Sem dados"

    # --- cluster / estilo (mantive sua lógica original, apenas renomeei retornos) ---
    try:
        metricas_estilo = [
            'tempo_luta_segundos',
            'iniciativa_pegada_diferenca',
            'shidos_atleta',
            'newaza_tentativas_diferenca',
            'sutemiwaza_tentativas_diferenca',
            'tewaza_tentativas_diferenca',
            'ashiwaza_tentativas_diferenca',
            'koshiwaza_tentativas_diferenca'
        ]
        perfis = df.groupby('atleta')[metricas_estilo].mean().fillna(0)
        estilo = "Sem dados"
        if len(perfis) >= 2:
            scaler = StandardScaler()
            perfis_scaled = scaler.fit_transform(perfis)
            n_clusters = min(4, len(perfis))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            perfis['Cluster'] = kmeans.fit_predict(perfis_scaled)

            centros = perfis.groupby('Cluster')[metricas_estilo].mean()
            medias_gerais = perfis[metricas_estilo].mean()

            nomes_clusters = {}
            for cluster_id in centros.index:
                linha = centros.loc[cluster_id]
                if linha['newaza_tentativas_diferenca'] > medias_gerais['newaza_tentativas_diferenca'] * 1.2:
                    nome = "Especialista de Chão"
                elif (linha['sutemiwaza_tentativas_diferenca'] > medias_gerais['sutemiwaza_tentativas_diferenca'] * 1.2) or (linha['shidos_atleta'] > 1.3):
                    nome = "Atleta de Risco"
                elif linha['tempo_luta_segundos'] < medias_gerais['tempo_luta_segundos'] * 0.9:
                    nome = "Lutas Rápidas"
                elif linha['iniciativa_pegada_diferenca'] > medias_gerais['iniciativa_pegada_diferenca']:
                    nome = "Brigador de Pegada"
                else:
                    nome = "Técnico / Equilibrado"
                nomes_clusters[cluster_id] = nome

            if atleta in perfis.index:
                cluster_atleta = int(perfis.loc[atleta]['Cluster'])
                estilo = nomes_clusters.get(cluster_atleta, "Sem dados")
    except Exception:
        estilo = "Sem dados"

    # --- Mapeamentos de texto que você pediu (descrições prontas) ---
    descricoes_estilos = {
        "Especialista de Chão": "Foca em levar a luta para o solo, onde tem vantagem estatística.",
        "Atleta de Risco": "Usa golpes de sacrifício ou joga no limite das punições.",
        "Lutas Rápidas": "Explosivo. Decide a luta (ou perde) nos primeiros minutos.",
        "Brigador de Pegada": "Domina o Kumi-kata para anular o oponente.",
        "Técnico / Equilibrado": "Atleta versátil sem um pico estatístico extremo nas categorias analisadas.",
        "Sem dados": "Sem dados"
    }

    # arma principal: frase padrão + pequeno parágrafo de análise
    analise_arma = " A vitória dele depende quase que exclusivamente de impor esse fundamento."

    # ponto fraco: frase padrão + conclusão
    conclusao_ponto_fraco = (
        f"O atleta aparenta ter dificuldades nesse fundamento e deve ser aprimorado. Atualmente, é uma ferramenta que normalmente não gera resultados para ele. Se o plano A falhar, ele não conta com esse recurso."
    )

    return {
        # chaves antigas (para compatibilidade)
        "dependencia_chave": dependencia_nome,
        "ponto_menos_decisivo": ponto_menos_nome,
        "estilo_atleta": estilo,
        "importancia": importancias.round(4).to_dict() if not importancias.empty else {},
        "acuracia": acuracia,

        # chaves novas/formatadas para frontend
        "arma_principal": {
            "nome": dependencia_nome,
            "titulo": "É definido por:",
            "analise": analise_arma
        },
        "ponto_fraco": {
            "nome": ponto_menos_nome,
            "titulo": "O atleta deixa a desejar em:",
            "conclusao": conclusao_ponto_fraco
        },
        "classificacao_final": {
            "nome": estilo,
            "descricao": descricoes_estilos.get(estilo, "Sem dados")
        }
    }
