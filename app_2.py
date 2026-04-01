import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Generador Taludes Scoops3D", layout="wide")

st.title("⛰️ Generador de Terreno y Nivel Freático para Scoops3D")
st.write("Define los perfiles 2D introduciendo puntos (X, Z). El programa interpolará las alturas, extruirá el modelo y generará los archivos Raster 3D (.asc).")

# --- 1. CONFIGURACIÓN DEL MODELO (SIDEBAR) ---
st.sidebar.header("⚙️ Parámetros del Raster")
tamano_celda = st.sidebar.number_input("Tamaño de celda (m)", min_value=0.1, value=1.0, step=0.5)
ancho_extrusion = st.sidebar.number_input("Ancho de extrusión [Eje Y] (m)", min_value=10.0, value=100.0, step=10.0)

# --- 2. ENTRADA DE DATOS (TABLAS INTERACTIVAS) ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("⛰️ Perfil del Terreno (X, Z)")
    st.write("Asegúrate de que la X vaya en aumento.")
    datos_terreno = {
        'X': [0.0, 15.0, 25.0, 35.0, 45.0, 60.0],
        'Z_Terreno': [0.0, 0.0, 10.0, 10.0, 20.0, 20.0]
    }
    df_terreno = st.data_editor(pd.DataFrame(datos_terreno), num_rows="dynamic", key="terr")

with col2:
    st.subheader("💧 Nivel Freático (X, Z)")
    st.write("Define por dónde va el agua subterránea.")
    datos_agua = {
        'X': [0.0, 20.0, 40.0, 60.0],
        'Z_Agua': [0.0, 2.0, 12.0, 15.0]
    }
    df_agua = st.data_editor(pd.DataFrame(datos_agua), num_rows="dynamic", key="agua")

# --- 3. PROCESAMIENTO E INTERPOLACIÓN ---
# Ordenar datos por si se introducen desordenados
df_terreno = df_terreno.sort_values(by='X')
df_agua = df_agua.sort_values(by='X')

# Usamos los límites del terreno para definir el tamaño de la cuadrícula
x_min = df_terreno['X'].iloc[0]
x_max = df_terreno['X'].iloc[-1]

# Calcular número de columnas (X) y filas (Y)
ncols = int((x_max - x_min) / tamano_celda) + 1
nrows = int(ancho_extrusion / tamano_celda) + 1

# Crear el eje X regular para la malla
perfil_x_regular = np.linspace(x_min, x_max, ncols)

# Interpolar ambos perfiles en la misma malla regular de X
perfil_z_terreno = np.interp(perfil_x_regular, df_terreno['X'], df_terreno['Z_Terreno'])
perfil_z_agua = np.interp(perfil_x_regular, df_agua['X'], df_agua['Z_Agua'])

# --- 4. VISUALIZACIÓN COMBINADA (PLOTLY) ---
st.subheader("📈 Vista previa del Modelo 2D")

# Juntamos los datos interpolados para graficarlos
df_grafico = pd.DataFrame({
    'Terreno': perfil_z_terreno,
    'Nivel Freático': perfil_z_agua
}, index=perfil_x_regular)

fig = px.line(
    df_grafico,
    markers=False,
    title="Perfil Interpolado: Terreno vs Agua (Usa la rueda para zoom)",
    labels={'index': 'Distancia X (m)', 'value': 'Elevación Z (m)', 'variable': 'Capa'}
)

# Forzar colores: Marrón (Tierra) y Azul (Agua)
fig.for_each_trace(lambda t: t.update(line=dict(color='#8B4513' if t.name == 'Terreno' else '#1E90FF')))

# Proporción 1:1 para que no se deforme la geometría visualmente
fig.update_yaxes(scaleanchor="x", scaleratio=1)

st.plotly_chart(fig, use_container_width=True)
st.write(f"**Dimensiones finales de los archivos 3D:** {ncols} columnas (X) × {nrows} filas (Y)")

# --- 5. EXTRUSIÓN Y GENERACIÓN DE ARCHIVOS ASCII ---
def generar_ascii(perfil_1d):
    # Extruir el perfil 2D (copiamos la fila 'nrows' veces)
    matriz_3d = np.tile(perfil_1d, (nrows, 1))
    
    # Formato estricto de encabezado
    encabezado = (
        f"ncols         {ncols}\n"
        f"nrows         {nrows}\n"
        f"xllcorner     {x_min:.3f}\n"
        f"yllcorner     0.000\n"
        f"cellsize      {tamano_celda}\n"
        f"NODATA_value  -9999\n"
    )
    
    # Formatear la matriz a texto (3 decimales)
    datos_texto = '\n'.join(' '.join(f"{val:.3f}" for val in fila) for fila in matriz_3d)
    return encabezado + datos_texto

# Generar los textos de ambos archivos
texto_terreno = generar_ascii(perfil_z_terreno)
texto_agua = generar_ascii(perfil_z_agua)

# --- 6. BOTONES DE DESCARGA ---
st.subheader("💾 Descargar Archivos para Scoops3D")
col_desc1, col_desc2 = st.columns(2)

with col_desc1:
    st.download_button(
        label="📥 Descargar DEM Terreno (.asc)",
        data=texto_terreno,
        file_name="topografia_scoops.asc",
        mime="text/plain"
    )

with col_desc2:
    st.download_button(
        label="📥 Descargar Raster Nivel Freático (.asc)",
        data=texto_agua,
        file_name="agua_scoops.asc",
        mime="text/plain"
    )