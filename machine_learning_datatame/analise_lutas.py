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
ATLETA_FOCO = "Atleta_Gama" #Atleta a ser analisado

def carregar_dados_completos(db_path, table_name):
    """Carrega todos os dados do banco de dados."""
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
    """Treina dois modelos (atleta vs. geral), avalia a precisão e compara a importância dos fatores."""
    print("\n" + "="*80)
    print(" ANÁLISE 1: PERFIL PREDITIVO (O QUE LEVA À VITÓRIA?)")
    print("="*80)

    df_atleta = df[df['atleta'] == atleta_foco].copy()
    df_outros = df[df['atleta'] != atleta_foco].copy()

    if len(df_atleta) < 20 or len(df_outros) < 50:
        print("AVISO: Dados insuficientes para uma análise preditiva comparativa robusta.")
        return

    features = [
        'tempo_luta_segundos', 'shidos_atleta',
        'newaza_tentativas_diferenca', 'newaza_acertos_diferenca',
        'tewaza_tentativas_diferenca', 'tewaza_acertos_diferenca',
        'koshiwaza_tentativas_diferenca', 'koshiwaza_acertos_diferenca',
        'ashiwaza_tentativas_diferenca', 'ashiwaza_acertos_diferenca',
        'sutemiwaza_tentativas_diferenca', 'sutemiwaza_acertos_diferenca',
        'iniciativa_pegada_diferenca', 'numero_pausas'
    ]
    
    #Modelo do Atleta
    print(f"\n--- Analisando Modelo para '{atleta_foco}' ---")
    X_atl = df_atleta[features]
    y_atl = df_atleta['resultado'].astype(int)
    
    X_train_atl, X_test_atl, y_train_atl, y_test_atl = train_test_split(X_atl, y_atl, test_size=0.3, random_state=42, stratify=y_atl)
    
    modelo_atleta = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    modelo_atleta.fit(X_train_atl, y_train_atl)
    y_pred_atl = modelo_atleta.predict(X_test_atl)


    print(f"Performance do Modelo '{atleta_foco}' (em dados de teste):")
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
    print("Performance do Modelo Geral (em dados de teste):")
    print(classification_report(y_test_ger, y_pred_ger, target_names=['Derrota', 'Vitoria'], zero_division=0))
    

    modelo_geral.fit(X_ger, y_ger)
    importancia_geral = pd.Series(modelo_geral.feature_importances_, index=features, name="Modelo_Geral")

    #Comparando
    df_comp = pd.concat([importancia_atleta, importancia_geral], axis=1).fillna(0)
    df_comp['Diferenca'] = df_comp[f"Modelo_{atleta_foco}"] - df_comp["Modelo_Geral"]
    df_comp = df_comp.sort_values(by=f"Modelo_{atleta_foco}", ascending=False)

    print("\n--- Comparativo de Importância dos Fatores (O que é mais importante para vencer?) ---")
    print(df_comp.to_string(float_format="%.3f"))
    
    print("\n--- Insights (Pontos Fracos e Fortes Quantificados) ---")
    dependencia = df_comp.sort_values(by='Diferenca', ascending=False).iloc[0]
    ponto_menos_decisivo = df_comp.sort_values(by='Diferenca', ascending=True).iloc[0]
    
    print(f"💪 DEPENDÊNCIA-CHAVE: O fator '{dependencia.name}' é MUITO mais importante para '{atleta_foco}' ({dependencia[f'Modelo_{atleta_foco}']:.1%}) do que para a média ({dependencia['Modelo_Geral']:.1%}). A vitória dele depende disso.")
    print(f"📉 PONTO MENOS DECISIVO (RELATIVO): O fator '{ponto_menos_decisivo.name}' é menos decisivo para '{atleta_foco}' ({ponto_menos_decisivo[f'Modelo_{atleta_foco}']:.1%}) do que para a média ({ponto_menos_decisivo['Modelo_Geral']:.1%}).")


def analisar_estilos_de_luta(df, atleta_foco):
    """Usa Clustering para identificar estilos de luta e posicionar o atleta."""
    print("\n" + "="*80)
    print(" ANÁLISE 2: PERFIL ESTRATÉGICO (QUAL O ESTILO DE LUTA?)")
    print("="*80)

    metricas_estilo = [
        'iniciativa_pegada_diferenca', 'shidos_atleta', 'wazari_diferenca',
        'tewaza_tentativas_diferenca', 'koshiwaza_tentativas_diferenca',
        'ashiwaza_tentativas_diferenca', 'newaza_tentativas_diferenca'
    ]
    
    perfis = df.groupby('atleta')[metricas_estilo].mean()

    if len(perfis) < 5:
        print("AVISO: Menos de 5 atletas no banco de dados. A análise de estilos pode não ser significativa.")
        return
        
    scaler = StandardScaler()
    perfis_scaled = scaler.fit_transform(perfis)

    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    perfis['Estilo'] = kmeans.fit_predict(perfis_scaled)

    print("--- Centros dos Estilos de Luta (O 'DNA' de cada grupo) ---")
    estilos_dna = perfis.groupby('Estilo')[metricas_estilo].mean()
    print(estilos_dna.to_string(float_format="%.2f"))
    print("\nINTERPRETAÇÃO:")
    print(" - Estilos com 'iniciativa_pegada' e 'tentativas' altas são AGRESSIVOS.")
    print(" - Estilos com 'wazari_diferenca' alta e 'tentativas' baixas são PRECISO / CONTRA-ATACANTES.")
    print(" - Estilos com 'shidos_atleta' alto são mais indisciplinados ou arriscados.")
    
    estilo_atleta_foco = perfis.loc[atleta_foco]['Estilo']
    
    print(f"\n--- Análise Preditiva do Atleta '{atleta_foco}' ---")
    print(f"🧠 PERFIL: O atleta '{atleta_foco}' pertence ao 'Estilo {estilo_atleta_foco}'.")
    print("Compare as médias dele com o DNA do seu estilo para ver se ele é um atleta típico do grupo.")

def main():
    """Função principal que orquestra a análise."""
    df_total = carregar_dados_completos(DB_FILE, TABLE_NAME)
    
    if df_total is not None:
        analisar_importancia_comparativa(df_total, ATLETA_FOCO)
        analisar_estilos_de_luta(df_total, ATLETA_FOCO)

if __name__ == "__main__":
    main()