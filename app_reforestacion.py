import streamlit as st
import pandas as pd
import subprocess
import os

st.set_page_config(page_title="Planeación Reforestación", layout="wide")
st.title("Planeación de Reforestación: Modelo Matemático y Heurístico")

st.sidebar.header("Parámetros de entrada")

# Selección de días de planeación
dias = st.sidebar.slider("Número de días de planeación", min_value=10, max_value=150, value=90, step=10)

# Selección de especies y polígonos
especies_lista = [
    "Agave lechuguilla", "Agave salmiana", "Agave scabra", "Agave striata",
    "Opuntia cantabrigiensis", "Opuntia engelmani", "Opuntia robusta",
    "Opuntia streptacanta", "Prosopis laevigata", "Yucca filifera"
]
poligonos_lista = ["p1", "p3", "p4", "p5", "p20", "p23", "p24", "p17", "p16", "p19"]

especies_seleccionadas = st.sidebar.multiselect("Selecciona las especies a considerar", especies_lista, default=especies_lista)
poligonos_seleccionados = st.sidebar.multiselect("Selecciona los polígonos a considerar", poligonos_lista, default=poligonos_lista)

# Botón para ejecutar modelos
if st.sidebar.button("Ejecutar modelos"):
    with st.spinner("Ejecutando modelos. Esto puede tardar unos minutos..."):

        # Guardar los parámetros en un archivo temporal o como variable global
        parametros = {
            "dias": dias,
            "especies": especies_seleccionadas,
            "poligonos": poligonos_seleccionados
        }

        # Llamar script matemático
        try:
            from modelo_matematico import run_modelo_matematico
            df_compras_math, df_entregas_math = run_modelo_matematico(parametros)
            st.session_state.resultados_matematico = (df_compras_math, df_entregas_math)
        except Exception as e:
            st.error(f"Error en el modelo matemático: {e}")
            st.session_state.resultados_matematico = None

        # Llamar script heurístico
        try:
            from modelo_heuristico import df_subrutas, df_compras, df_indicadores
            st.session_state.resultados_heuristico = (df_subrutas, df_compras, df_indicadores)
        except Exception as e:
            st.error(f"Error en el modelo heurístico: {e}")
            st.session_state.resultados_heuristico = None

# Visualización de resultados
st.subheader("Resultados")
modelo = st.radio("Selecciona el modelo a visualizar", ["Matemático", "Heurístico"])

if modelo == "Matemático":
    if "resultados_matematico" in st.session_state and st.session_state.resultados_matematico:
        df_compras_math, df_entregas_math = st.session_state.resultados_matematico
        st.write("### Compras")
        st.dataframe(df_compras_math)
        st.write("### Entregas")
        st.dataframe(df_entregas_math)
    else:
        st.warning("No se encontraron resultados del modelo matemático.")

elif modelo == "Heurístico":
    if "resultados_heuristico" in st.session_state and st.session_state.resultados_heuristico:
        df_subrutas, df_compras, df_indicadores = st.session_state.resultados_heuristico
        st.write("### Subrutas")
        st.dataframe(df_subrutas)
        st.write("### Compras")
        st.dataframe(df_compras)
        st.write("### Indicadores de desempeño")
        st.dataframe(df_indicadores)
    else:
        st.warning("No se encontraron resultados del modelo heurístico.")
