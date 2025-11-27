import pandas as pd
import sqlite3
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score

#Conexao om o banco de dados
DB_FILE = "lutas.db"
TABLE_NAME = "lutas"
ATLETA_FOCO = "Aristides" #Atleta a ser analisado

NOMES = {
    'tempo_luta_segundos': 'Duração da Luta',
    'shidos_atleta': 'Faltas (Shidos)',
    'numero_pausas': 'Ritmo (Pausas)',
    'iniciativa_pegada_diferenca': 'Controle de Pegada',
    'newaza_tentativas_diferenca': 'Técnicas no Solo (Ne-waza)',
    'tewaza_tentativas_diferenca': 'Técnicas de Braço (Te-waza)',
    'koshiwaza_tentativas_diferenca': 'Técnicas de Quadril (Koshi-waza)',
    'ashiwaza_tentativas_diferenca': 'Técnicas de Perna (Ashi-waza)',
    'sutemiwaza_tentativas_diferenca': 'Técnicas de Sacrifício (Sutemi-waza)'
}

def carregar_dados_completos(db_path, table_name):
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        query = f"SELECT * FROM {table_name}"
        df = pd.read_sql_query(query, conn)
        print(f"--- Carregados {len(df)} registros de luta de {df['atleta'].nunique()} atletas. ---")
        return df
    except Exception as e:
        print(f"ERRO ao carregar dados: {e}")
        return None
    finally:
        if conn:
            conn.close()

def analisar_importancia_comparativa(df, atleta_foco):
    print("\n" + "="*80)
    print(" ANÁLISE 1: PERFIL PREDITIVO (O QUE LEVA À VITÓRIA?)")
    print("="*80)

    df_atleta = df[df['atleta'] == atleta_foco].copy()
    df_outros = df[df['atleta'] != atleta_foco].copy()

    if len(df_atleta) < 20 or len(df_outros) < 50:
        print("AVISO: Dados insuficientes para a análise preditiva.")
        return

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
    
    #Modelo do Atleta
    print(f"\n--- Analisando Modelo para '{atleta_foco}' ---")
    X_atl = df_atleta[features]
    y_atl = df_atleta['resultado'].astype(int)
    
    X_train_atl, X_test_atl, y_train_atl, y_test_atl = train_test_split(X_atl, y_atl, test_size=0.3, random_state=42, stratify=y_atl)
    
    modelo_atleta = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    modelo_atleta.fit(X_train_atl, y_train_atl)
    y_pred_atl = modelo_atleta.predict(X_test_atl)


    print(f"Performance do Modelo '{atleta_foco}':")
    print(classification_report(y_test_atl, y_pred_atl, target_names=['Derrota', 'Vitoria'], zero_division=0))
    

    modelo_atleta.fit(X_atl, y_atl)
    importancia_atleta = pd.Series(modelo_atleta.feature_importances_, index=features, name=f"Modelo_{atleta_foco}")


    print(f"\n--- Analisando Modelo Geral (Outros Atletas) ---")
    X_ger = df_outros[features]
    y_ger = df_outros['resultado'].astype(int)


    X_train_ger, X_test_ger, y_train_ger, y_test_ger = train_test_split(X_ger, y_ger, test_size=0.3, random_state=42, stratify=y_ger)
    
    modelo_geral = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    modelo_geral.fit(X_train_ger, y_train_ger)
    y_pred_ger = modelo_geral.predict(X_test_ger)

    #Relatorio
    print("Performance do Modelo Geral:")
    print(classification_report(y_test_ger, y_pred_ger, target_names=['Derrota', 'Vitoria'], zero_division=0))
    

    modelo_geral.fit(X_ger, y_ger)
    importancia_geral = pd.Series(modelo_geral.feature_importances_, index=features, name="Modelo_Geral")

    #Comparando
    df_comp = pd.concat([importancia_atleta, importancia_geral], axis=1).fillna(0)
    df_comp['Diferenca'] = df_comp[f"Modelo_{atleta_foco}"] - df_comp["Modelo_Geral"]
    df_comp = df_comp.sort_values(by=f"Modelo_{atleta_foco}", ascending=False)


  
    df_comp = df_comp.rename(index=NOMES)

    print("\n--- Comparativo de Fatores (O que decide a vitória?) ---")
    cols_to_print = [f"Modelo_{atleta_foco}", "Modelo_Geral", "Diferenca"]
    print((df_comp[cols_to_print] * 100).to_string(float_format="%.1f %%"))
    
    print("\n" + "-"*80)
    print(f"RELATÓRIO DE INTELIGÊNCIA PARA: {atleta_foco.upper()}")
    print("-"*(36 + len(atleta_foco)))

  
    dependencia = df_comp.sort_values(by='Diferenca', ascending=False).iloc[0]
    ponto_fraco = df_comp.sort_values(by='Diferenca', ascending=True).iloc[0]
    
  
    fator_chave = dependencia.name
    importancia_atleta = dependencia[f"Modelo_{atleta_foco}"] * 100 
    importancia_geral = dependencia["Modelo_Geral"] * 100

    print(f"1. ARMA PRINCIPAL: O jogo de '{atleta_foco}' é definido por: {fator_chave.upper()}.")
    print(f"   - Importância para ele: {importancia_atleta:.1f}% (Média geral: {importancia_geral:.1f}%)")
    print(f"   - Análise: A vitória dele depende quase que exclusivamente de impor esse fundamento.")


    nome_fraco = ponto_fraco.name
    imp_fraco_atl = ponto_fraco[f"Modelo_{atleta_foco}"] * 100
    imp_fraco_ger = ponto_fraco["Modelo_Geral"] * 100

    print(f"\n2.  PONTO FRACO (Gap Técnico): O atleta deixa a desejar em: {nome_fraco.upper()}.")
    print(f"   - Uso efetivo para vitória: Apenas {imp_fraco_atl:.1f}% (Enquanto a média usa {imp_fraco_ger:.1f}%)")
    print(f"   - Conclusão: O atleta aparenta ter dificuldades nesse fundamento e deve ser aprimorado. Atualmente, é uma ferramenta que normalmente não gera resultados para ele. Se o plano A falhar, ele não conta com esse recurso.")


def analisar_estilos_de_luta(df, atleta_foco):
    print("\n" + "="*80)
    print(" ANÁLISE 2: PERFIL ESTRATÉGICO (QUAL O ESTILO DE LUTA?)")
    print("="*80)

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
    
    # Agrupa médias por atleta
    perfis = df.groupby('atleta')[metricas_estilo].mean()

    if len(perfis) < 2:
        print("AVISO: Poucos dados para criar clusters.")
        return
        
    scaler = StandardScaler()
    perfis_scaled = scaler.fit_transform(perfis)

    n_clusters_possiveis = min(4, len(perfis) - 1) if len(perfis) > 1 else 1
    
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    
    try:
        perfis['Cluster'] = kmeans.fit_predict(perfis_scaled)
    except:
        kmeans = KMeans(n_clusters=len(perfis)-1, random_state=42, n_init=10)
        perfis['Cluster'] = kmeans.fit_predict(perfis_scaled)

    nomes_clusters = {} 
    
    centros = perfis.groupby('Cluster')[metricas_estilo].mean()
    medias_gerais = perfis[metricas_estilo].mean()

    for cluster_id in centros.index:
        linha_cluster = centros.loc[cluster_id]
        
        # Estilos de Luta
        
        if linha_cluster['newaza_tentativas_diferenca'] > medias_gerais['newaza_tentativas_diferenca'] * 1.2:
            nome = " Especialista de Chão"
    
        elif (linha_cluster['sutemiwaza_tentativas_diferenca'] > medias_gerais['sutemiwaza_tentativas_diferenca'] * 1.2) or \
             (linha_cluster['shidos_atleta'] > 1.3): 
            nome = " Atleta de Risco"

        elif linha_cluster['tempo_luta_segundos'] < medias_gerais['tempo_luta_segundos'] * 0.9:
            nome = " Estilo Lutas Rápidas"

        elif linha_cluster['iniciativa_pegada_diferenca'] > medias_gerais['iniciativa_pegada_diferenca']:
            nome = " Brigador de Pegada"
            
        else:
            nome = " Técnico / Equilibrado"

        nomes_clusters[cluster_id] = nome

    # Aplica os nomes no DataFrame
    perfis['Nome_Estilo'] = perfis['Cluster'].map(nomes_clusters)

    print("--- Definição dos Estilos Encontrados ---")
    resumo = perfis.groupby('Nome_Estilo')[metricas_estilo].mean()
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    print(resumo.to_string(float_format="%.2f"))

    # Análise do Atleta Foco
    if atleta_foco in perfis.index:
        estilo_atleta = perfis.loc[atleta_foco]['Nome_Estilo']
        
        print(f"\n" + "-"*80)
        print(f"🧠 CLASSIFICAÇÃO FINAL: O atleta '{atleta_foco}' foi identificado como:")
        print(f"   >> {estilo_atleta.upper()} <<")
        print("-" * 80)
        
        if "Chão" in estilo_atleta:
            print(" Característica: Foca em levar a luta para o solo, onde tem vantagem estatística.")
        elif "Risco" in estilo_atleta:
            print(" Característica: Usa golpes de sacrifício ou joga no limite das punições.")
        elif "Rápidas" in estilo_atleta:
            print(" Característica: Explosivo. Decide a luta (ou perde) nos primeiros minutos.")
        elif "Pegada" in estilo_atleta:
            print(" Característica: Domina o Kumi-kata para anular o oponente.")
        else:
            print(" Característica: Atleta versátil sem um pico estatístico extremo nas categorias analisadas.")
    else:
        print(f"AVISO: O atleta '{atleta_foco}' não foi encontrado nos perfis de estilo.")

def main():
    """Função principal que orquestra a análise."""
    df_total = carregar_dados_completos(DB_FILE, TABLE_NAME)
    
    if df_total is not None:
        analisar_importancia_comparativa(df_total, ATLETA_FOCO)
        analisar_estilos_de_luta(df_total, ATLETA_FOCO)

if __name__ == "__main__":
    main()