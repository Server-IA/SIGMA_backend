import csv
import random

# =========================
# 0. SEED
# =========================
random.seed(3)

# =========================
# 1. Constantes generales
# =========================
R = 287.05       # Constante de gas específico del aire (J/kg·K)
rho0 = 1.225     # Densidad del aire a nivel del mar (kg/m³)
alpha = 0.05     # Factor velocidad para implemento
g = 9.81         # Gravedad (m/s²)

# =========================
# 2. Rango de variables (POTENCIA DISPONIBLE)
# =========================
Pnominal_range = (20, 400)      # Potencia nominal del tractor
p_range = (101900, 102200)      # Presión atmosférica (Pa)
T_range = (297, 301)            # Temperatura (K)

# =========================
# 3. Datos base para IMPLEMENTO
# =========================
implementos = [
    {"nombre": "arado_vertedera", "k_base": 5500, "n": 1.0},
    {"nombre": "arado_disco", "k_base": 4200, "n": 1.0},
    {"nombre": "cincel_chisel", "k_base": 4000, "n": 1.1},
    {"nombre": "subsolador", "k_base": 10000, "n": 1.2},
    {"nombre": "rastra_discos", "k_base": 2400, "n": 0.9},
    {"nombre": "cultivador_campo", "k_base": 1800, "n": 0.9},
    {"nombre": "sembradora_directa", "k_base": 500, "n": 0.7},
    {"nombre": "rodillo_compactador", "k_base": 900, "n": 0.7},
]

# Multiplicadores textura
texturas = {"arcilla": 1.25, "franco": 1.00, "arenoso": 0.90}

# Multiplicadores humedad
def humedad_factor(h):
    if h <= 15:
        return 0.95
    elif 16 <= h <= 25:
        return 1.00
    elif 26 <= h <= 35:
        return 1.10
    else:
        return 1.20

# Rango de variables para implemento
ancho_range = (0.5, 3.0)        # metros
profundidad_range = (0.1, 0.5)  # metros
velocidad_range = (3, 10)       # km/h
humedad_range = (5, 50)         # %

# =========================
# 4. Rango de variables (RESISTENCIA POR PENDIENTE)
# =========================
masa_range = (2000, 10000)      # kg
pendiente_range = (0, 30)      # %

# =========================
# 5. Matriz de COEFICIENTE DE RODADURA (Crr)
# =========================
Crr_tabla = {
    "Arena":      {"baja": 0.02,  "media": 0.03,  "alta": 0.04,  "muy_alta": 0.05},
    "Franco":     {"baja": 0.03,  "media": 0.04,  "alta": 0.05,  "muy_alta": 0.06},
    "Arcilla":    {"baja": 0.04,  "media": 0.05,  "alta": 0.06,  "muy_alta": 0.07},
    "Asfalto":    {"baja": 0.01,  "media": 0.015, "alta": 0.02,  "muy_alta": None},
}

def rango_humedad(h):
    if h < 15:
        return "baja"
    elif 15 <= h < 25:
        return "media"
    elif 25 <= h < 35:
        return "alta"
    else:
        return "muy_alta"

# =========================
# 6. Parámetros para CORRECCIÓN POR SLIP
# =========================
ks = 1.0                   # Coeficiente empírico
slip_range = (0.0, 0.25)   # Slip entre 0% y 25%

# =========================
# 7. Rango de eficiencia de TRANSMISIÓN
# =========================
n_transmision_range = (0.80, 0.90)  # 80–90%

# =========================
# 8. Parámetros de CONSUMO DE COMBUSTIBLE
# =========================
rpm_range = (1400, 2200)   # rpm promedio

# Densidad de diésel según T (°C)
def densidad_diesel(temp_c):
    if temp_c <= 0:
        return 0.842
    elif temp_c <= 5:
        return 0.838
    elif temp_c <= 10:
        return 0.834
    elif temp_c <= 15:
        return 0.832
    elif temp_c <= 20:
        return 0.828
    elif temp_c <= 25:
        return 0.824
    elif temp_c <= 30:
        return 0.820
    elif temp_c <= 35:
        return 0.816
    elif temp_c <= 40:
        return 0.812
    elif temp_c <= 45:
        return 0.808
    elif temp_c <= 50:
        return 0.804
    elif temp_c <= 55:
        return 0.800
    else:           # ≥60
        return 0.796

# Tabla BSFC (g/kWh) según carga (%) y rpm
BSFC_tabla = {
    1400: {25: 340, 50: 280, 75: 240, 100: 260},
    1600: {25: 320, 50: 260, 75: 230, 100: 240},
    1800: {25: 310, 50: 250, 75: 225, 100: 230},
    2000: {25: 330, 50: 270, 75: 235, 100: 240},
    2200: {25: 350, 50: 290, 75: 250, 100: 260},
}

def interp_lineal(x, x1, y1, x2, y2):
    """Interpolación lineal simple"""
    return y1 + (y2 - y1) * ((x - x1) / (x2 - x1))

def obtener_bsfc(rpm, carga):
    # Interpolar entre RPMs
    rpm_keys = sorted(BSFC_tabla.keys())
    # Buscar RPM inferior y superior
    for i in range(len(rpm_keys) - 1):
        if rpm_keys[i] <= rpm <= rpm_keys[i + 1]:
            rpm_low = rpm_keys[i]
            rpm_high = rpm_keys[i + 1]
            break
    else:
        rpm_low, rpm_high = rpm_keys[0], rpm_keys[-1]

    # Interpolar en carga para cada rpm
    def interp_carga(rpm_key):
        c_keys = sorted(BSFC_tabla[rpm_key].keys())
        for j in range(len(c_keys) - 1):
            if c_keys[j] <= carga <= c_keys[j + 1]:
                return interp_lineal(carga, c_keys[j], BSFC_tabla[rpm_key][c_keys[j]],
                                     c_keys[j + 1], BSFC_tabla[rpm_key][c_keys[j + 1]])
        return BSFC_tabla[rpm_key][c_keys[-1]]

    bsfc_low = interp_carga(rpm_low)
    bsfc_high = interp_carga(rpm_high)

    return round(interp_lineal(rpm, rpm_low, bsfc_low, rpm_high, bsfc_high), 2)

# =========================
# 9. Generar datos
# =========================
n_datos = 5000
datos = []

for _ in range(n_datos):
    # ----------- 1. POTENCIA DISPONIBLE -----------
    Pnominal = round(random.uniform(*Pnominal_range), 2)
    p = round(random.uniform(*p_range), 2)
    T = round(random.uniform(*T_range), 2)
    T_C = round(T - 273.15, 2)

    rho = round(p / (R * T), 2)
    delta = round(rho / rho0, 2)
    Pdisp = round(Pnominal * delta, 2)

    # ----------- 2. DRAFT DEL IMPLEMENTO -----------
    impl = random.choice(implementos)
    k_base = round(impl["k_base"], 2)
    n = round(impl["n"], 2)
    nombre_impl = impl["nombre"]

    textura = random.choice(list(texturas.keys()))
    M_textura = round(texturas[textura], 2)

    ancho = round(random.uniform(*ancho_range), 2)
    profundidad = round(random.uniform(*profundidad_range), 2)
    v = round(random.uniform(*velocidad_range), 2)  # km/h
    humedad = round(random.uniform(*humedad_range), 2)
    M_humedad = round(humedad_factor(humedad), 2)

    Kimpl = round(
        k_base
        * M_textura
        * M_humedad
        * (profundidad / 0.20) ** n
        * (1 + alpha * (v - 5)),
        2
    )

    Dimpl = round(Kimpl * ancho * profundidad, 2)

    # ----------- 3. RESISTENCIA POR PENDIENTE -----------
    masa_total = round(random.uniform(*masa_range), 2)
    pendiente = round(random.uniform(*pendiente_range), 2)
    Rpend = round(masa_total * g * (pendiente / 100), 2)

    # ----------- 4. RESISTENCIA A LA RODADURA -----------
    tipo_suelo = random.choice(list(Crr_tabla.keys()))
    rango_hum = rango_humedad(humedad)
    Crr = Crr_tabla[tipo_suelo][rango_hum]

    while Crr is None:
        tipo_suelo = random.choice(list(Crr_tabla.keys()))
        rango_hum = rango_humedad(humedad)
        Crr = Crr_tabla[tipo_suelo][rango_hum]

    Crr = round(Crr, 4)  # 4 decimales para Crr
    Rrod = round(Crr * masa_total * g, 2)

    # ----------- 5. CORRECCIÓN POR SLIP -----------
    S = round(random.uniform(*slip_range), 2)
    Def = round(Dimpl * (1 + ks * S), 2)
    vef = round(v * (1 - S), 2)  # km/h

    # ----------- 6. FUERZA TOTAL -----------
    Ftotal = round(Def + Rpend + Rrod, 2)

    # ----------- 7. POTENCIA REQUERIDA -----------
    vef_m_s = round(vef * 1000 / 3600, 4)
    Ptrac = round((Ftotal * vef_m_s) / 1000, 2)  # kW
    n_transmision = round(random.uniform(*n_transmision_range), 2)
    Pmotor = round(Ptrac / n_transmision, 2)     # kW

    # ----------- 8. CONSUMO DE COMBUSTIBLE -----------
    Pdiesel = densidad_diesel(T_C)
    rpm = round(random.uniform(*rpm_range), 0)
    carga = round((Pmotor / Pnominal) * 100, 2)  # %
    BSFC = obtener_bsfc(rpm, carga)              # g/kWh
    consumo_horario = round((BSFC * Pmotor) / (Pdiesel * 1000), 2)  # L/h
    duracion = round(random.uniform(1, 8), 2)    # h
    consumo_total = round(consumo_horario * duracion, 2)            # L

    # ----------- UNIR TODO EN UNA SOLA FILA -----------
    fila = [
        Pnominal, p, T, T_C, rho, delta, Pdisp,
        "",
        nombre_impl, k_base, n, ancho, profundidad,
        textura, M_textura, humedad, M_humedad, v,
        Kimpl, Dimpl,
        "",
        masa_total, pendiente, Rpend,
        "",
        tipo_suelo, rango_hum, Crr, Rrod,
        "",
        ks, S, Def, vef, vef_m_s,
        "",
        Ftotal,
        "",
        Ptrac, n_transmision, Pmotor,
        "",
        Pdiesel, rpm, carga, BSFC, consumo_horario, duracion, consumo_total
    ]
    datos.append(fila)

# =========================
# 10. Exportar a CSV
# =========================
nombre_archivo = "datos_maquinaria_consumo.csv"

with open(nombre_archivo, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "Pnominal(kW)", "p(Pa)", "T(K)", "T(°C)", "rho", "delta", "Pdisp(kW)",
        "",
        "Implemento", "k_base", "n", "Ancho(m)", "Profundidad(m)",
        "Textura", "M_textura", "Humedad(%)", "M_humedad", "Velocidad(km/h)",
        "Kimpl", "Dimpl",
        "",
        "Masa_total(kg)", "Pendiente(%)", "Rpend(N)",
        "",
        "Tipo_suelo", "Rango_humedad", "Crr", "Rrod(N)",
        "",
        "ks", "Slip", "Def(N)", "vef(km/h)", "vef_m_s(m/s)",
        "",
        "Ftotal(N)",
        "",
        "Ptrac(kW)", "n_transmision", "Pmotor(kW)",
        "",
        "Pdiesel(g/cm³)", "RPM", "Carga(%)", "BSFC(g/kWh)",
        "Consumo_horario(L/h)", "Duracion(h)", "Consumo_total(L)"
    ])
    writer.writerows(datos)

print(f"Archivo CSV generado con {n_datos} datos: {nombre_archivo}")
