from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, LpStatus
import pandas as pd
from collections import defaultdict
import re

def run_modelo_matematico(parametros):
    I = list(range(10))
    J = list(range(10))
    T = list(range(parametros["dias"]))
    P = list(range(4))
    R = list(range(1, 50))

    especies = [
        "Agave lechuguilla", "Agave salmiana", "Agave scabra", "Agave striata",
        "Opuntia cantabrigiensis", "Opuntia engelmani", "Opuntia robusta",
        "Opuntia streptacanta", "Prosopis laevigata", "Yucca filifera"
    ]

    poligonos = ["p1", "p3", "p4", "p5", "p20", "p23", "p24", "p17", "p16", "p19"]
    proveedores = ["Vivero", "Moctezuma", "Venado", "Laguna Seca"]

    HA = [33, 157, 33, 33, 39, 30, 58, 51, 69, 21]
    Demanda = {i: [HA[i]] * 10 for i in I}

    demanda_total = defaultdict(lambda: defaultdict(float))
    for i in I:
        for j in J:
            demanda_total[i][j] = Demanda[i][j]

    volumen_unitario = [502.65, 284.83, 62.83, 122.72, 122.72,
                        122.72, 122.72, 212.06, 212.06, 122.72]
    ttiempo = [1 if i in [0, 1, 2, 3, 8, 9] else 0.33 for i in I]
    cap_transporte = 8000
    cap_almacenamiento = 400 * 10000
    costo_plantar = 20
    costo_inventario = 1
    jornada_max = 6
    carga_descarga_unitaria = 0.05
    MAX_SUBRUTAS_POR_DIA = 80

    CostoCompra = [ [None, None, None, 26], [None, None, None, 26], [None, 26, None, 26],
                    [None, 26, 25, None], [None, 17, 18, None], [None, None, 18, 21],
                    [None, 17, 18, 18], [None, None, 18, None], [26.5, None, None, None],
                    [26, None, None, None] ]

    poligono_id = {"p1": 0, "p3": 1, "p4": 2, "p5": 3, "p20": 4, 
                   "p23": 5, "p24": 6, "p17": 7, "p16": 8, "p19": 9}

    df_rutas = pd.read_excel("rutas_todas_las_demandas.xlsx")
    especie_idx = {esp: i for i, esp in enumerate(especies)}

    subruta_poligonos = defaultdict(set)
    tiempo_subruta = defaultdict(dict)

    for _, row in df_rutas.iterrows():
        especie = row['Demanda']
        subruta = int(row['Subruta'])
        especie_i = especie_idx[especie]
        tray = str(row['Trayectoria'])
        tiempo = float(row['Tiempo (h)'])

        pols = re.findall(r'p\d+', tray)
        ids = [poligono_id[p] for p in pols if p in poligono_id]

        for pid in ids:
            subruta_poligonos[(especie_i, subruta)].add(pid)
        tiempo_subruta[especie_i][subruta] = tiempo

    subruta_poligonos = {k: list(v) for k, v in subruta_poligonos.items()}

    model = LpProblem("Modelo_Reforestacion_Subrutas", LpMinimize)
    xipt = LpVariable.dicts("xipt", (I, P, T), lowBound=0)
    yijt = LpVariable.dicts("yijt", (I, J, T), lowBound=0)
    invit = LpVariable.dicts("invit", (I, T), lowBound=0)
    zirt = LpVariable.dicts("zirt", (I, R, T), cat=LpBinary)

    peso_tiempo = {t: 1 + (t / max(T)) for t in T}

    model += (
        lpSum(xipt[i][p][t] * ttiempo[i] for i in I for p in P for t in T) +
        lpSum(yijt[i][j][t] * costo_plantar for i in I for j in J for t in T) +
        lpSum(invit[i][t] * costo_inventario for i in I for t in T) +
        lpSum(zirt[i][r][t] * tiempo_subruta[i].get(r, 0) for i in I for r in R for t in T) +
        lpSum(xipt[i][p][t] * CostoCompra[i][p] for i in I for p in P for t in T if CostoCompra[i][p] is not None) +
        lpSum(yijt[i][j][t] * peso_tiempo[t] for i in I for j in J for t in T)
    )

    for i in I:
        for p in P:
            if CostoCompra[i][p] is None:
                for t in T:
                    model += xipt[i][p][t] == 0

    for i in I:
        for t in T:
            compras = lpSum(xipt[i][p][t] for p in P)
            entregas = lpSum(yijt[i][j][t] for j in J)
            if t == 0:
                model += invit[i][t] == compras - entregas
            else:
                model += invit[i][t] == invit[i][t-1] + compras - entregas

    for i in I:
        for j in J:
            model += lpSum(yijt[i][j][t] for t in T) >= demanda_total[i][j]

    for t in T:
        model += lpSum(invit[i][t] * volumen_unitario[i] for i in I) <= cap_almacenamiento

    for i in I:
        for t in T:
            model += lpSum(yijt[i][j][t] for j in J) <= cap_transporte

    for t in T:
        model += lpSum(yijt[i][j][t] for i in I for j in J) <= 3000

    for i in I:
        for t in T:
            model += lpSum(zirt[i][r][t] for r in R) <= 50

    for t in T:
        model += lpSum(zirt[i][r][t] for i in I for r in R) <= MAX_SUBRUTAS_POR_DIA

    for t in T:
        tratamiento_bin = lpSum(zirt[i][r][t] * ttiempo[i] for i in I for r in R)
        carga_descarga = lpSum(yijt[i][j][t] * carga_descarga_unitaria for i in I for j in J)
        ruta = lpSum(zirt[i][r][t] * tiempo_subruta[i].get(r, 0) for i in I for r in R)
        model += tratamiento_bin + carga_descarga + ruta <= jornada_max

    for i in I:
        for j in J:
            for t in T:
                if t >= 3:
                    compras_validas = lpSum(xipt[i][p][s] for p in P for s in range(max(0, t-7), t-2))
                    model += yijt[i][j][t] <= compras_validas
                else:
                    model += yijt[i][j][t] == 0

    model.solve()

    compras = []
    entregas = []

    for i in I:
        for p in P:
            for t in T:
                var = xipt[i][p][t]
                if var.varValue and var.varValue > 0:
                    compras.append({
                        "Día": t+1,
                        "Especie": especies[i],
                        "Proveedor": proveedores[p],
                        "Cantidad comprada": int(round(var.varValue))
                    })

    for i in I:
        for j in J:
            for t in T:
                var = yijt[i][j][t]
                if var.varValue and var.varValue > 0:
                    entregas.append({
                        "Día": t+1,
                        "Especie": especies[i],
                        "Polígono": poligonos[j],
                        "Cantidad entregada": int(round(var.varValue))
                    })

    df_compras = pd.DataFrame(compras)
    df_entregas = pd.DataFrame(entregas)

    return df_compras, df_entregas
