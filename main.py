import streamlit as st
import pandas as pd

# Importar resultados heurísticos directamente
from modelo_heuristico import df_subrutas, df_compras, df_indicadores, df_inventario, df_secuencia

# Importar función del modelo matemático
from modelo_matematico import run_modelo_matematico

st.set_page_config(page_title="Planeación Reforestación", layout="wide")
st.title("Planeación de Reforestación: Modelo Matemático y Heurístico")

# Subida de archivo Excel
st.subheader("Carga de archivo Excel")
archivo_subido = st.file_uploader("Sube el archivo Excel con las hojas: Especies, Demandas y Parámetros", type=["xlsx"])

# Sidebar con parámetros
st.sidebar.header("Parámetros de entrada")
dias = st.sidebar.slider("Número de días de planeación", min_value=10, max_value=150, value=90, step=10)

especies_lista_default = [
    "Agave lechuguilla", "Agave salmiana", "Agave scabra", "Agave striata",
    "Opuntia cantabrigiensis", "Opuntia engelmani", "Opuntia robusta",
    "Opuntia streptacanta", "Prosopis laevigata", "Yucca filifera"
]
poligonos_lista_default = ["p1", "p3", "p4", "p5", "p20", "p23", "p24", "p17", "p16", "p19"]

especies_seleccionadas = st.sidebar.multiselect("Selecciona las especies a considerar", especies_lista_default, default=especies_lista_default)
poligonos_seleccionados = st.sidebar.multiselect("Selecciona los polígonos a considerar", poligonos_lista_default, default=poligonos_lista_default)

modelo_a_ejecutar = st.sidebar.radio("Selecciona el modelo a ejecutar", ["Matemático", "Heurístico"])

# Botón de ejecución
if st.sidebar.button("Ejecutar modelos"):
    if archivo_subido is not None:
        with st.spinner("Procesando archivo..."):
            try:
                hoja1 = pd.read_excel(archivo_subido, sheet_name=0)
                hoja2 = pd.read_excel(archivo_subido, sheet_name=1)
                hoja3 = pd.read_excel(archivo_subido, sheet_name=2)

                hoja1.columns = hoja1.columns.str.strip()
                hoja2.columns = hoja2.columns.str.strip()
                hoja3.columns = hoja3.columns.str.strip()

                especies = hoja1["Especies"].tolist()
                volumen_cm3 = {fila["Especies"]: float(fila["Volumen"]) for _, fila in hoja1.iterrows()}
                altura_cm = {fila["Especies"]: float(fila["Altura"]) for _, fila in hoja1.iterrows()}

                poligonos = hoja2["Poligonos"].tolist()
                demandas = hoja2.drop(columns="Poligonos").transpose().values.tolist()

                capacidad_m2 = float(hoja3.iloc[0, 1])

                if modelo_a_ejecutar == "Matemático":
                    parametros = {
                        "dias": dias,
                        "especies": especies_seleccionadas,
                        "poligonos": poligonos_seleccionados
                    }
                    df_compras_math, df_entregas_math = run_modelo_matematico(parametros)
                    st.session_state.resultados_matematico = (df_compras_math, df_entregas_math)

                elif modelo_a_ejecutar == "Heurístico":
                    # Como el heurístico se importa ya ejecutado, solo se guarda en sesión
                    st.session_state.resultados_heuristico = (df_subrutas, df_compras, df_indicadores)

            except Exception as e:
                st.error(f"❌ Error al procesar el archivo o ejecutar el modelo: {e}")
                st.stop()
    else:
        st.warning("⚠️ Por favor, sube un archivo Excel antes de ejecutar el modelo.")
        st.stop()

# Visualización
st.subheader("Resultados")

if modelo_a_ejecutar == "Matemático":
    if "resultados_matematico" in st.session_state:
        df_compras_math, df_entregas_math = st.session_state.resultados_matematico
        st.write("### Compras (Modelo Matemático)")
        st.dataframe(df_compras_math)
        st.write("### Entregas (Modelo Matemático)")
        st.dataframe(df_entregas_math)
    else:
        st.warning("No hay resultados del modelo matemático.")

elif modelo_a_ejecutar == "Heurístico":
    if archivo_subido is not None:
        with st.spinner("Procesando archivo y ejecutando modelo heurístico..."):
            try:
                with open("archivo_temporal.xlsx", "wb") as f:
                    f.write(archivo_subido.getbuffer())

                from modelo_heuristico import df_subrutas, df_compras, df_indicadores, df_inventario, df_secuencia

                st.session_state.resultados_heuristico = (
                    df_subrutas, df_compras, df_indicadores, df_inventario, df_secuencia
                )

            except Exception as e:
                st.error(f"❌ Error en el modelo heurístico: {e}")
                st.stop()
    else:
        st.warning("⚠️ Debes subir un archivo Excel antes de ejecutar el modelo heurístico.")
        st.stop()
        
    if "resultados_heuristico" in st.session_state:
        df_subrutas, df_compras, df_indicadores, df_inventario, df_secuencia = st.session_state.resultados_heuristico

        st.write("### Subrutas (Modelo Heurístico)")
        st.dataframe(df_subrutas)

        st.write("### Compras (Modelo Heurístico)")
        st.dataframe(df_compras)

        st.write("### Indicadores de Desempeño")
        st.dataframe(df_indicadores)

        st.write("### Trazabilidad de Inventario")
        st.dataframe(df_inventario)

        st.write("### Monitoreo de Secuencia")
        st.dataframe(df_secuencia)
    else:
        st.warning("No hay resultados del modelo heurístico.")

