import pandas as pd
import numpy as np
import math

archivo_excel = "Template.xlsx"  
hoja1 = pd.read_excel(archivo_excel, sheet_name=0)  
hoja2 = pd.read_excel(archivo_excel, sheet_name=1)  
hoja3 = pd.read_excel(archivo_excel, sheet_name=2)  

hoja1.columns = hoja1.columns.str.strip()
hoja2.columns = hoja2.columns.str.strip()
hoja3.columns = hoja3.columns.str.strip()

# ========= Hoja 1 =========
especies = hoja1["Especies"].tolist()
volumen_cm3 = {fila["Especies"]: float(fila["Volumen"]) for _, fila in hoja1.iterrows()}
altura_cm = {fila["Especies"]: float(fila["Altura"]) for _, fila in hoja1.iterrows()}

# ========= Hoja 2 =========
poligonos = hoja2["Poligonos"].tolist()
demandas = hoja2.drop(columns="Poligonos").transpose().values.tolist()

# ========= Hoja 3 =========
capacidad_m2 = 3.25

def generar_subrutas_hibridas(
    df_demanda,
    capacidad_por_especie,
    indice_poligono,
    indice_a_poligono,
    Tiempos,
    JORNADA_LABORAL_MIN,
    TIEMPO_CARGA_DESCARGA,
    duracion_tratamiento,
    PREFERENCIA_PRIORIDAD
):
    subrutas_data = []
    df_demanda = df_demanda.copy()
    df_demanda["Demanda_restante"] = df_demanda["Demanda_total"]
    dia_actual = 3
    subruta_id = 1
    tiempo_dia = 0
    especies_entregadas_en_dia = set()

    while df_demanda["Demanda_restante"].sum() > 0:
        especies = df_demanda[df_demanda["Demanda_restante"] > 0]["Especie"].unique().tolist()
        avanzamos = False

        for especie in especies:
            if especie not in capacidad_por_especie:
                continue

            df_esp = df_demanda[(df_demanda["Especie"] == especie) & (df_demanda["Demanda_restante"] > 0)].copy()
            df_esp["Índice"] = df_esp["Polígono"].map(indice_poligono)
            df_esp = df_esp.sort_values(by=["Demanda_restante"], ascending=False)

            demanda_pendiente = df_esp.set_index("Índice")["Demanda_restante"].to_dict()
            capacidad_restante = capacidad_por_especie[especie]
            pos_actual = 0
            tiempo_subruta = 0
            entregas_subruta = []

            if especie not in especies_entregadas_en_dia:
                tiempo_tratamiento = duracion_tratamiento[especie]
                if tiempo_dia + tiempo_tratamiento >= JORNADA_LABORAL_MIN:
                    dia_actual += 1
                    tiempo_dia = 0
                    especies_entregadas_en_dia = set()
                    tiempo_tratamiento = duracion_tratamiento[especie]
                tiempo_dia += tiempo_tratamiento
                especies_entregadas_en_dia.add(especie)
            else:
                tiempo_tratamiento = 0

            while capacidad_restante > 0 and demanda_pendiente:
                if PREFERENCIA_PRIORIDAD == "demanda":
                    candidatos = sorted(demanda_pendiente.items(), key=lambda x: (-x[1], Tiempos[pos_actual][x[0]]))
                else:
                    candidatos = sorted(demanda_pendiente.items(), key=lambda x: (Tiempos[pos_actual][x[0]], -x[1]))

                seleccionado = None
                tiempo_total_ruta = tiempo_subruta

                for idx, demanda in candidatos:
                    tiempo_estimado = Tiempos[pos_actual][idx] * 60
                    tiempo_regreso = Tiempos[idx][0] * 60
                    if tiempo_dia + tiempo_total_ruta + tiempo_estimado + tiempo_regreso + TIEMPO_CARGA_DESCARGA <= JORNADA_LABORAL_MIN:
                        seleccionado = idx
                        break

                if seleccionado is None:
                    break

                cantidad = min(math.ceil(demanda_pendiente[seleccionado]), math.floor(capacidad_restante))
                entregas_subruta.append((indice_a_poligono[seleccionado], cantidad, especie))
                capacidad_restante -= cantidad
                tiempo_viaje = Tiempos[pos_actual][seleccionado] * 60
                tiempo_subruta += tiempo_viaje
                pos_actual = seleccionado

                df_demanda.loc[
                    (df_demanda["Polígono"] == indice_a_poligono[seleccionado]) & (df_demanda["Especie"] == especie),
                    "Demanda_restante"
                ] -= cantidad
                del demanda_pendiente[seleccionado]
                avanzamos = True

            if entregas_subruta:
                tiempo_regreso = Tiempos[pos_actual][0] * 60
                duracion_total = tiempo_subruta + tiempo_regreso + TIEMPO_CARGA_DESCARGA
                tiempo_dia += duracion_total

                for pol, cant, esp in entregas_subruta:
                    subrutas_data.append({
                        "Día": dia_actual,
                        "Subruta": subruta_id,
                        "Especie": esp,
                        "Polígono": pol,
                        "Cantidad entregada": cant,
                        "Duración tratamiento (min)": tiempo_tratamiento,
                        "Duración subruta (min)": round(duracion_total, 2),
                        "Duración total (min)": round(tiempo_tratamiento + duracion_total, 2)
                    })
                subruta_id += 1

            if tiempo_dia >= JORNADA_LABORAL_MIN:
                dia_actual += 1
                tiempo_dia = 0
                especies_entregadas_en_dia = set()

        if not avanzamos:
            dia_actual += 1
            tiempo_dia = 0
            especies_entregadas_en_dia = set()

    return pd.DataFrame(subrutas_data)

def generar_subrutas_hibridas(
    df_demanda,
    capacidad_por_especie,
    indice_poligono,
    indice_a_poligono,
    Tiempos,
    JORNADA_LABORAL_MIN,
    TIEMPO_CARGA_DESCARGA,
    duracion_tratamiento,
    PREFERENCIA_PRIORIDAD
):
    subrutas_data = []
    df_demanda = df_demanda.copy()
    df_demanda["Demanda_restante"] = df_demanda["Demanda_total"]
    dia_actual = 3
    subruta_id = 1
    tiempo_dia = 0
    especies_entregadas_en_dia = set()

    while df_demanda["Demanda_restante"].sum() > 0:
        especies = df_demanda[df_demanda["Demanda_restante"] > 0]["Especie"].unique().tolist()
        avanzamos = False

        for especie in especies:
            if especie not in capacidad_por_especie:
                continue

            df_esp = df_demanda[(df_demanda["Especie"] == especie) & (df_demanda["Demanda_restante"] > 0)].copy()
            df_esp["Índice"] = df_esp["Polígono"].map(indice_poligono)
            df_esp = df_esp.sort_values(by=["Demanda_restante"], ascending=False)

            demanda_pendiente = df_esp.set_index("Índice")["Demanda_restante"].to_dict()
            capacidad_restante = capacidad_por_especie[especie]
            pos_actual = 0
            tiempo_subruta = 0
            entregas_subruta = []

            if especie not in especies_entregadas_en_dia:
                tiempo_tratamiento = duracion_tratamiento[especie]
                if tiempo_dia + tiempo_tratamiento >= JORNADA_LABORAL_MIN:
                    dia_actual += 1
                    tiempo_dia = 0
                    especies_entregadas_en_dia = set()
                    tiempo_tratamiento = duracion_tratamiento[especie]
                tiempo_dia += tiempo_tratamiento
                especies_entregadas_en_dia.add(especie)
            else:
                tiempo_tratamiento = 0

            while capacidad_restante > 0 and demanda_pendiente:
                if PREFERENCIA_PRIORIDAD == "demanda":
                    candidatos = sorted(demanda_pendiente.items(), key=lambda x: (-x[1], Tiempos[pos_actual][x[0]]))
                else:
                    candidatos = sorted(demanda_pendiente.items(), key=lambda x: (Tiempos[pos_actual][x[0]], -x[1]))

                seleccionado = None
                tiempo_total_ruta = tiempo_subruta

                for idx, demanda in candidatos:
                    tiempo_estimado = Tiempos[pos_actual][idx] * 60
                    tiempo_regreso = Tiempos[idx][0] * 60
                    if tiempo_dia + tiempo_total_ruta + tiempo_estimado + tiempo_regreso + TIEMPO_CARGA_DESCARGA <= JORNADA_LABORAL_MIN:
                        seleccionado = idx
                        break

                if seleccionado is None:
                    break

                cantidad = min(math.ceil(demanda_pendiente[seleccionado]), math.floor(capacidad_restante))
                entregas_subruta.append((indice_a_poligono[seleccionado], cantidad, especie))
                capacidad_restante -= cantidad
                tiempo_viaje = Tiempos[pos_actual][seleccionado] * 60
                tiempo_subruta += tiempo_viaje
                pos_actual = seleccionado

                df_demanda.loc[
                    (df_demanda["Polígono"] == indice_a_poligono[seleccionado]) & (df_demanda["Especie"] == especie),
                    "Demanda_restante"
                ] -= cantidad
                del demanda_pendiente[seleccionado]
                avanzamos = True

            if entregas_subruta:
                tiempo_regreso = Tiempos[pos_actual][0] * 60
                duracion_total = tiempo_subruta + tiempo_regreso + TIEMPO_CARGA_DESCARGA
                tiempo_dia += duracion_total

                for pol, cant, esp in entregas_subruta:
                    subrutas_data.append({
                        "Día": dia_actual,
                        "Subruta": subruta_id,
                        "Especie": esp,
                        "Polígono": pol,
                        "Cantidad entregada": cant,
                        "Duración tratamiento (min)": tiempo_tratamiento,
                        "Duración subruta (min)": round(duracion_total, 2),
                        "Duración total (min)": round(tiempo_tratamiento + duracion_total, 2)
                    })
                subruta_id += 1

            if tiempo_dia >= JORNADA_LABORAL_MIN:
                dia_actual += 1
                tiempo_dia = 0
                especies_entregadas_en_dia = set()

        if not avanzamos:
            dia_actual += 1
            tiempo_dia = 0
            especies_entregadas_en_dia = set()

    return pd.DataFrame(subrutas_data)

def generar_compras(df_subrutas, parametros, volumen_cm3, altura_cm, capacidad_max_m2):
    """
    Genera el DataFrame de compras a partir de las subrutas, aplicando un límite por capacidad del almacén (en m^2).

    Parámetros:
        df_subrutas (pd.DataFrame): DataFrame con las entregas por día.
        parametros (dict): Parámetros con costos y días de aclimatación.
        volumen_cm3 (dict): Volumen por especie en cm^3.
        altura_cm (dict): Altura por especie en cm.
        capacidad_max_m2 (float): Capacidad máxima del almacén (por día) en m^2.

    Retorna:
        df_compras (pd.DataFrame): Compras limitadas por espacio disponible.
    """
    # Paso 1: calcular día de pedido por especie
    df_subrutas = df_subrutas.copy()
    df_subrutas["Día_pedido"] = df_subrutas["Día"] - parametros["dias_aclimatacion"]

    df_compras = (
        df_subrutas.groupby(["Día_pedido", "Especie"])
        .agg({"Cantidad entregada": "sum"})
        .reset_index()
    )

    # Paso 2: asignar proveedor más barato y costo unitario
    def proveedor_minimo(especie):
        proveedores = parametros["costos_proveedor"].get(especie, {})
        return min(proveedores.items(), key=lambda x: x[1])[0] if proveedores else None

    def costo_unitario(especie):
        proveedores = parametros["costos_proveedor"].get(especie, {})
        return min(proveedores.values()) if proveedores else None

    df_compras["Proveedor"] = df_compras["Especie"].apply(proveedor_minimo)
    df_compras["Costo unitario"] = df_compras["Especie"].apply(costo_unitario)
    df_compras["Costo total"] = df_compras["Cantidad entregada"] * df_compras["Costo unitario"]

    # Paso 3: aplicar la restricción de espacio máximo en m² por día
    area_por_planta = {
        especie: volumen_cm3[especie] / altura_cm[especie] / 10000
        for especie in volumen_cm3
    }

    dias = sorted(df_compras["Día_pedido"].unique())
    ocupacion_diaria_m2 = {dia: 0 for dia in dias}
    compras_filtradas = []

    for _, row in df_compras.iterrows():
        especie = row["Especie"]
        dia = row["Día_pedido"]
        cantidad = row["Cantidad entregada"]
        area_indiv = area_por_planta[especie]
        espacio_disponible = capacidad_max_m2 - ocupacion_diaria_m2[dia]

        # Máximo número de plantas posibles ese día
        max_cantidad = int(espacio_disponible // area_indiv)
        cantidad_final = min(cantidad, max_cantidad)

        if cantidad_final > 0:
            ocupacion_diaria_m2[dia] += cantidad_final * area_indiv
            nueva_fila = row.copy()
            nueva_fila["Cantidad entregada"] = cantidad_final
            nueva_fila["Costo total"] = cantidad_final * row["Costo unitario"]
            compras_filtradas.append(nueva_fila)

    df_compras_limitadas = pd.DataFrame(compras_filtradas)

    return df_compras_limitadas

def generar_inventario(df_compras, df_subrutas, volumen_cm3, altura_cm):
    """
    Genera el inventario diario por especie y área ocupada en m^2.

    Returns:
        df_inventario: DataFrame con columnas por especie (inicio, fin, m2) y total m^2 por día.
        df_inventario_largo: DataFrame en formato largo con columnas [Día, Especie, Inicio, Fin, m_2 ocupados].
    """
    dias = sorted(set(df_compras["Día_pedido"]) | set(df_subrutas["Día"]))
    especies = df_compras["Especie"].unique()

    # Inicializar inventarios por día
    inventario_inicio = {especie: [0] * (max(dias) + 10) for especie in especies}
    inventario_fin = {especie: [0] * (max(dias) + 10) for especie in especies}

    # Registrar entradas (día pedido + 1)
    for _, row in df_compras.iterrows():
        dia = row["Día_pedido"] + 1
        inventario_inicio[row["Especie"]][dia] += row["Cantidad entregada"]

    df_inventario = pd.DataFrame({"Día": list(range(len(next(iter(inventario_inicio.values())))))})
    registros_largos = []

    for especie in especies:
        dias_totales = len(inventario_inicio[especie])
        inicio_dia = [0] * dias_totales
        fin_dia = [0] * dias_totales

        for d in range(dias_totales):
            inicio_dia[d] = 0 if d == 0 else fin_dia[d - 1]
            inicio_dia[d] += inventario_inicio[especie][d]
            entregas_dia = df_subrutas[(df_subrutas["Día"] == d) & (df_subrutas["Especie"] == especie)]["Cantidad entregada"].sum()
            fin_dia[d] = inicio_dia[d] - entregas_dia

        area_por_planta = volumen_cm3[especie] / altura_cm[especie] / 10000
        m2_ocupados = [round(fin * area_por_planta, 3) for fin in fin_dia]

        # Agregar columnas al DataFrame ancho
        df_inventario[f"{especie}_inicio"] = inicio_dia
        df_inventario[f"{especie}_fin"] = fin_dia
        df_inventario[f"{especie}_m2"] = m2_ocupados



    # Calcular m² totales al final del día
    df_inventario["m2_totales"] = df_inventario[[col for col in df_inventario.columns if col.endswith("_m2")]].sum(axis=1)

   
    return df_inventario

def generar_indicador_desempeno_final(df_subrutas):
    """
    Genera un resumen de desempeño con horas totales trabajadas y días usados.

    Parámetros:
        df_subrutas (pd.DataFrame): DataFrame con entregas y columna 'Duración total (min)'.

    Retorna:
        df_desempeno_final (pd.DataFrame): contiene horas_totales_trabajados y dias_totales_usados.
    """
    minutos_totales_trabajados = df_subrutas.groupby("Día")["Duración total (min)"].sum().sum()
    dias_totales = df_subrutas["Día"].nunique()

    df_desempeno_final = pd.DataFrame({
        "horas_totales_trabajados": [round(minutos_totales_trabajados, 2) / 60],
        "dias_totales_usados": [dias_totales]
    })

    return df_desempeno_final

# Crear lista estructurada
data = []
for especie, demanda_especie in zip(especies, demandas):
    for poligono, cantidad in zip(poligonos, demanda_especie):
        data.append({
            "Especie": especie,
            "Polígono": poligono,
            "Demanda_total": int(np.ceil(cantidad))
        })

# Crear DataFrame final
df_demanda = pd.DataFrame(data)

df_demanda

capacidad_cm2 = capacidad_m2 * 10_000

# Capacidad máxima por especie
capacidad_por_especie = {
    especie: capacidad_cm2 / (volumen_cm3[especie] / altura_cm[especie])
    for especie in volumen_cm3
}

# Índices de polígonos
poligonos = df_demanda["Polígono"].unique().tolist()
indice_poligono = {p: i + 1 for i, p in enumerate(poligonos)}
indice_a_poligono = {v: k for k, v in indice_poligono.items()}

# Tiempos reales
Tiempos = [
  [0, 0.0745, 0.063, 0.061, 0.06, 0.05, 0.022, 0.011, 0.012, 0.025, 0.033, 0.045, 0.058],
  [0.0745, 0, 0.024, 0.016, 0.014, 0.088, 0.08, 0.078, 0.069, 0.067, 0.08, 0.095, 0.011],
  [0.063, 0.024, 0, 0.011, 0.022, 0.067, 0.064, 0.065, 0.063, 0.065, 0.08, 0.095, 0.06],
  [0.061, 0.016, 0.011, 0, 0.011, 0.073, 0.065, 0.064, 0.057, 0.058, 0.072, 0.087, 0.103],
  [0.06, 0.014, 0.022, 0.011, 0, 0.079, 0.067, 0.065, 0.0055, 0.053, 0.066, 0.082, 0.096],
  [0.05, 0.088, 0.067, 0.0073, 0.079, 0, 0.029, 0.04, 0.061, 0.073, 0.083, 0.095, 0.107],
  [0.022, 0.08, 0.064, 0.065, 0.067, 0.029, 0, 0.011, 0.034, 0.047, 0.056, 0.066, 0.079],
  [0.011, 0.078, 0.065, 0.064, 0.065, 0.04, 0.011, 0, 0.024, 0.037, 0.045, 0.055, 0.068],
  [0.012, 0.069, 0.063, 0.057, 0.055, 0.061, 0.034, 0.024, 0, 0.013, 0.023, 0.036, 0.046],
  [0.025, 0.067, 0.065, 0.058, 0.053, 0.073, 0.047, 0.037, 0.013, 0, 0.015, 0.03, 0.045],
  [0.033, 0.08, 0.08, 0.072, 0.066, 0.083, 0.056, 0.045, 0.023, 0.015, 0, 0.016, 0.021],
  [0.045, 0.095, 0.095, 0.065, 0.082, 0.095, 0.066, 0.055, 0.036, 0.03, 0.016, 0, 0.015],
  [0.058, 0.011, 0.06, 0.0103, 0.096, 0.107, 0.079, 0.068, 0.046, 0.045, 0.021, 0.015, 0],
]

# Parámetros de operación
JORNADA_LABORAL_MIN = 360
TIEMPO_CARGA_DESCARGA = 60
import pandas as pd

# Crear tabla de tratamientos parametrizados
# Nopales siempre llevan tratamiento de 20 min
# El resto puede tener tratamiento de 60 min si se indica que están en bolsa

# Lista base de especies y tipo de tratamiento (default 0)
especies_tratamiento = {
    "Agave lechuguilla": 0,
    "Agave salmiana": 0,
    "Agave scabra": 0,
    "Agave striata": 0,
    "Opuntia cantabrigiensis": 20,
    "Opuntia engelmani": 20,
    "Opuntia robusta": 20,
    "Opuntia streptacanta": 20,
    "Prosopis laevigata": 0,
    "Yucca filifera": 0
}

# Lista de plantas que se marcarán como "en bolsa" (puede modificarse dinámicamente)
plantas_en_bolsa = [
    "Agave lechuguilla",
    "Agave salmiana",
    "Agave striata",
    "Prosopis laevigata"
]

# Agregar 60 minutos de tratamiento a plantas en bolsa
for especie in plantas_en_bolsa:
    especies_tratamiento[especie] += 60

# Crear DataFrame para visualización y uso posterior
df_tratamientos = pd.DataFrame([
    {"Especie": especie, "Tratamiento (min)": tiempo}
    for especie, tiempo in especies_tratamiento.items()
])


# Configuración editable
PARAMETROS = {
    "dias_aclimatacion": 3,
    "max_dias_almacen": 7,
    "capacidad_almacen_m2": 400,
    "tratamientos_especie": {
        "Opuntia cantabrigiensis": {"tratamiento_extra_min": 20},
        "Opuntia engelmani": {"tratamiento_extra_min": 20},
        "Opuntia robusta": {"tratamiento_extra_min": 20},
        "Opuntia streptacanta": {"tratamiento_extra_min": 20}
    },
    "costos_proveedor": {
        "Agave lechuguilla": {"Laguna seca": 26},
        "Agave salmiana": {"Laguna seca": 26},
        "Agave scabra": {"Moctezuma": 26, "Laguna seca": 26},
        "Agave striata": {"Moctezuma": 26, "Venado": 25},
        "Opuntia cantabrigiensis": {"Moctezuma": 17, "Venado": 18, "Laguna seca": 21},
        "Opuntia engelmani": {"Venado": 18, "Laguna seca": 18},
        "Opuntia robusta": {"Moctezuma": 17, "Venado": 18},
        "Opuntia streptacanta": {"Venado": 18},
        "Prosopis laevigata": {"Vivero": 26.5},
        "Yucca filifera": {"Vivero": 26}
    }
}


duracion_tratamiento = {
    especie: 60 if especie in plantas_en_bolsa else 20 if "Opuntia" in especie else 0
    for especie in capacidad_por_especie
}

# Preferencia en la heurística greedy: "demanda" o "distancia"
PREFERENCIA_PRIORIDAD = "distancia"  # o "distancia"


capacidad_max_almacen = 400

df_subrutas = generar_subrutas_hibridas(
    df_demanda,
    capacidad_por_especie,
    indice_poligono,
    indice_a_poligono,
    Tiempos,
    JORNADA_LABORAL_MIN,
    TIEMPO_CARGA_DESCARGA,
    duracion_tratamiento,
    PREFERENCIA_PRIORIDAD
)
df_subrutas

df_compras = generar_compras(df_subrutas, PARAMETROS, volumen_cm3, altura_cm, capacidad_max_almacen)
df_compras

df_inventario = generar_inventario(df_compras, df_subrutas, volumen_cm3, altura_cm)
df_inventario

df_indicadores = generar_indicador_desempeno_final(df_subrutas)
df_indicadores

def generar_secuencia_diaria_con_compras_e_ingresos(df_subrutas, df_inventario, df_compras, df_demanda):
    """
    Genera un registro por día de cada acción logística:
    - Compra (pedido al proveedor)
    - Ingreso al inventario (día siguiente al pedido)
    - Entrega (salida del almacén hacia plantación)

    Incluye: Día, Tipo, Especie, Cantidad, Inventario inicio y fin, Tratamiento, Polígono (si aplica),
    Demanda entregada acumulada y restante, con base en df_demanda.
    """
    registros = []

    # Demanda total por especie y por especie/polígono
    demanda_total_especie = df_demanda.groupby("Especie")["Demanda_total"].sum().to_dict()
    demanda_total_poligono = df_demanda.set_index(["Especie", "Polígono"])["Demanda_total"].to_dict()

    # Inicializar entregas acumuladas
    entregas_acumuladas_especie = {esp: 0 for esp in demanda_total_especie}
    entregas_acumuladas_poligono = {key: 0 for key in demanda_total_poligono}

    for _, row in df_compras.iterrows():
        especie = row["Especie"]
        dia_pedido = row["Día_pedido"]
        dia_llegada = dia_pedido + 1
        cantidad = row["Cantidad entregada"]

        col_inicio = f"{especie}_inicio"
        col_fin = f"{especie}_fin"

        inicio_llegada = df_inventario.loc[df_inventario["Día"] == dia_llegada, col_inicio].values[0] if dia_llegada in df_inventario["Día"].values else 0
        fin_llegada = df_inventario.loc[df_inventario["Día"] == dia_llegada, col_fin].values[0] if dia_llegada in df_inventario["Día"].values else 0

        registros.append({
            "Día": dia_pedido,
            "Tipo": "Compra",
            "Especie": especie,
            "Cantidad": cantidad,
            "Polígono": None,
            "Inventario inicio": None,
            "Inventario fin": None,
            "Tratamiento (min)": 0,
            "Demanda entregada acumulada": entregas_acumuladas_especie[especie],
            "Demanda restante": demanda_total_especie[especie] - entregas_acumuladas_especie[especie]
        })

        registros.append({
            "Día": dia_llegada,
            "Tipo": "Ingreso",
            "Especie": especie,
            "Cantidad": cantidad,
            "Polígono": None,
            "Inventario inicio": inicio_llegada,
            "Inventario fin": fin_llegada,
            "Tratamiento (min)": 0,
            "Demanda entregada acumulada": entregas_acumuladas_especie[especie],
            "Demanda restante": demanda_total_especie[especie] - entregas_acumuladas_especie[especie]
        })

    for _, row in df_subrutas.iterrows():
        dia = row["Día"]
        especie = row["Especie"]
        poligono = row["Polígono"]
        cantidad = row["Cantidad entregada"]
        tratamiento = row["Duración tratamiento (min)"]

        col_inicio = f"{especie}_inicio"
        col_fin = f"{especie}_fin"

        inicio = df_inventario.loc[df_inventario["Día"] == dia, col_inicio].values[0] if dia in df_inventario["Día"].values else 0
        fin = df_inventario.loc[df_inventario["Día"] == dia, col_fin].values[0] if dia in df_inventario["Día"].values else 0

        entregas_acumuladas_especie[especie] += cantidad
        entregas_acumuladas_poligono[(especie, poligono)] += cantidad

        registros.append({
            "Día": dia,
            "Tipo": "Entrega",
            "Especie": especie,
            "Cantidad": cantidad,
            "Polígono": poligono,
            "Inventario inicio": inicio,
            "Inventario fin": fin,
            "Tratamiento (min)": tratamiento,
            "Demanda entregada acumulada": entregas_acumuladas_especie[especie],
            "Demanda restante": demanda_total_especie[especie] - entregas_acumuladas_especie[especie]
        })

    df_secuencia = pd.DataFrame(registros).sort_values(by=["Día", "Tipo"]).reset_index(drop=True)
    return df_secuencia

df_secuencia = generar_secuencia_diaria_con_compras_e_ingresos(df_subrutas, df_inventario, df_compras, df_demanda)