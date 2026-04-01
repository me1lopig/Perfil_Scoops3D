import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador Taludes Scoops3D", layout="wide")

st.title("⛰️ Generador Avanzado para Scoops3D (Terreno, Agua y Estratos)")
st.write("Modifica los perfiles en las pestañas de la izquierda. El modelo 3D se generará automáticamente.")

# --- 1. CONFIGURACIÓN DEL RASTER (SIDEBAR) ---
st.sidebar.header("⚙️ Parámetros del Raster")
tamano_celda = st.sidebar.number_input("Tamaño de celda (m)", min_value=0.1, value=1.0, step=0.5)
ancho_extrusion = st.sidebar.number_input("Ancho de extrusión [Eje Y] (m)", min_value=10.0, value=100.0, step=10.0)

# --- 2. LAYOUT PRINCIPAL CON PESTAÑAS Y GRÁFICO ---
col_datos, col_grafico = st.columns([1, 2.5]) # Columna derecha aún más ancha

with col_datos:
    st.subheader("📝 Editor de Perfiles")
    
    # Creamos pestañas para no saturar la pantalla
    tab_terr, tab_agua, tab_estrato = st.tabs(["⛰️ Terreno", "💧 Agua", "🪨 Estrato Base"])
    
    with tab_terr:
        st.write("Superficie del modelo.")
        datos_terreno = {'X': [0.0, 15.0, 25.0, 35.0, 45.0, 60.0], 'Z_Terreno': [0.0, 0.0, 10.0, 10.0, 20.0, 20.0]}
        df_terreno = st.data_editor(pd.DataFrame(datos_terreno), num_rows="dynamic", key="terr", use_container_width=True)
        
    with tab_agua:
        st.write("Superficie del nivel freático.")
        datos_agua = {'X': [0.0, 20.0, 40.0, 60.0], 'Z_Agua': [0.0, 2.0, 12.0, 15.0]}
        df_agua = st.data_editor(pd.DataFrame(datos_agua), num_rows="dynamic", key="agua", use_container_width=True)

    with tab_estrato:
        st.write("Límite inferior de la Capa 1 (Ej. Roca).")
        # Por defecto, ponemos la roca base unos metros por debajo de la superficie
        datos_estrato = {'X': [0.0, 20.0, 40.0, 60.0], 'Z_Estrato': [-5.0, -5.0, 5.0, 8.0]}
        df_estrato = st.data_editor(pd.DataFrame(datos_estrato), num_rows="dynamic", key="estrato", use_container_width=True)

# --- 3. PROCESAMIENTO E INTERPOLACIÓN ---
# Ordenar siempre las X
df_terreno = df_terreno.sort_values(by='X')
df_agua = df_agua.sort_values(by='X')
df_estrato = df_estrato.sort_values(by='X')

x_min = df_terreno['X'].iloc[0]
x_max = df_terreno['X'].iloc[-1]

ncols = int((x_max - x_min) / tamano_celda) + 1
nrows = int(ancho_extrusion / tamano_celda) + 1

perfil_x_regular = np.linspace(x_min, x_max, ncols)

# Interpolar los 3 perfiles
perfil_z_terreno = np.interp(perfil_x_regular, df_terreno['X'], df_terreno['Z_Terreno'])
perfil_z_agua = np.interp(perfil_x_regular, df_agua['X'], df_agua['Z_Agua'])
perfil_z_estrato = np.interp(perfil_x_regular, df_estrato['X'], df_estrato['Z_Estrato'])

# --- 4. VISUALIZACIÓN EN TIEMPO REAL ---
with col_grafico:
    st.subheader("📈 Vista del Modelo 2D")
    
    df_grafico = pd.DataFrame({
        'Terreno': perfil_z_terreno,
        'Nivel Freático': perfil_z_agua,
        'Base Capa 1 (Roca)': perfil_z_estrato
    }, index=perfil_x_regular)

    fig = px.line(
        df_grafico,
        markers=False,
        labels={'index': 'Distancia X (m)', 'value': 'Elevación Z (m)', 'variable': 'Superficies'}
    )
    
    # Asignamos colores: Marrón (Tierra), Azul (Agua), Gris oscuro (Roca/Estrato base)
    colores = {'Terreno': '#8B4513', 'Nivel Freático': '#1E90FF', 'Base Capa 1 (Roca)': '#696969'}
    fig.for_each_trace(lambda t: t.update(line=dict(color=colores[t.name])))
    
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    st.plotly_chart(fig, use_container_width=True)

# --- 5. EXTRUSIÓN Y GENERACIÓN DE ARCHIVOS ASCII ---
def generar_ascii(perfil_1d):
    matriz_3d = np.tile(perfil_1d, (nrows, 1))
    encabezado = (
        f"ncols         {ncols}\n"
        f"nrows         {nrows}\n"
        f"xllcorner     {x_min:.3f}\n"
        f"yllcorner     0.000\n"
        f"cellsize      {tamano_celda}\n"
        f"NODATA_value  -9999\n"
    )
    datos_texto = '\n'.join(' '.join(f"{val:.3f}" for val in fila) for fila in matriz_3d)
    return encabezado + datos_texto

# Generamos los tres textos
texto_terreno = generar_ascii(perfil_z_terreno)
texto_agua = generar_ascii(perfil_z_agua)
texto_estrato = generar_ascii(perfil_z_estrato)

# --- 6. ZONA DE DESCARGAS ---
st.markdown("---")
st.subheader("💾 Descargar Archivos de Proyecto")
st.info(f"Dimensión de los mapas 3D: **{ncols} columnas × {nrows} filas**")

col_desc1, col_desc2, col_desc3 = st.columns(3)

with col_desc1:
    st.download_button("📥 1. DEM Terreno (.asc)", texto_terreno, "1_topografia.asc", "text/plain", use_container_width=True)
with col_desc2:
    st.download_button("📥 2. DEM Nivel Freático (.asc)", texto_agua, "2_agua.asc", "text/plain", use_container_width=True)
with col_desc3:
    st.download_button("📥 3. DEM Base Estrato 1 (.asc)", texto_estrato, "3_estrato1.asc", "text/plain", use_container_width=True)