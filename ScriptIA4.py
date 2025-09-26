import csv
import random

# =========================
# 0. SEED
# =========================
random.seed(2)

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
pendiente_range = (0, 30)       # %

# =========================
# 5. Matriz de COEFICIENTE DE RODADURA (Crr)
# =========================
Crr_tabla = {
    "Arena":      {"baja": 0.02,  "media": 0.03,  "alta": 0.04,  "muy_alta": 0.05},
    "Franco":     {"baja": 0.03,  "media": 0.04,  "alta": 0.05,  "muy_alta": 0.06},
    "Arcilla":    {"baja": 0.04,  "media": 0.05,  "alta": 0.06,  "muy_alta": 0.07},
    "Asfalto":    {"baja": 0.01,  "media": 0.015, "alta": 0.02,  "muy_alta": None},
}

# Función para determinar rango de humedad para Crr
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
# 6. Generar datos
# =========================
n_datos = 10000
datos = []

for _ in range(n_datos):
    # ----------- PRIMERA FORMULA: Potencia disponible -----------
    Pnominal = round(random.uniform(*Pnominal_range), 4)
    p = round(random.uniform(*p_range), 4)
    T = round(random.uniform(*T_range), 4)

    rho = round(p / (R * T), 4)
    delta = round(rho / rho0, 4)
    Pdisp = round(Pnominal * delta, 4)

    # ----------- SEGUNDA FORMULA: Draft del implemento -----------
    impl = random.choice(implementos)
    k_base = round(impl["k_base"], 4)
    n = round(impl["n"], 4)
    nombre_impl = impl["nombre"]

    textura = random.choice(list(texturas.keys()))
    M_textura = round(texturas[textura], 4)

    ancho = round(random.uniform(*ancho_range), 4)
    profundidad = round(random.uniform(*profundidad_range), 4)
    v = round(random.uniform(*velocidad_range), 4)
    humedad = round(random.uniform(*humedad_range), 4)
    M_humedad = round(humedad_factor(humedad), 4)

    Kimpl = round(
        k_base
        * M_textura
        * M_humedad
        * (profundidad / 0.20) ** n
        * (1 + alpha * (v - 5)),
        4
    )

    Dimpl = round(Kimpl * ancho * profundidad, 4)

    # ----------- TERCERA FORMULA: Resistencia por pendiente -----------
    masa_total = round(random.uniform(*masa_range), 4)
    pendiente = round(random.uniform(*pendiente_range), 4)

    Rpend = round(masa_total * g * (pendiente / 100), 4)

    # ----------- CUARTA FORMULA: Resistencia a la rodadura -----------
    tipo_suelo = random.choice(list(Crr_tabla.keys()))
    rango_hum = rango_humedad(humedad)
    Crr = Crr_tabla[tipo_suelo][rango_hum]

    # Si el valor es None (como en asfalto con humedad muy alta), se escoge otro válido
    while Crr is None:
        tipo_suelo = random.choice(list(Crr_tabla.keys()))
        rango_hum = rango_humedad(humedad)
        Crr = Crr_tabla[tipo_suelo][rango_hum]

    Crr = round(Crr, 4)
    Rrod = round(Crr * masa_total * g, 4)

    # ----------- UNIR TODO EN UNA SOLA FILA -----------
    fila = [
        # Datos primera fórmula
        Pnominal, p, T, rho, delta, Pdisp,

        "",

        # Datos segunda fórmula
        nombre_impl, k_base, n, ancho, profundidad,
        textura, M_textura, humedad, M_humedad, v,
        Kimpl, Dimpl,

        "",

        # Datos tercera fórmula
        masa_total, pendiente, Rpend,

        "",

        # Datos cuarta fórmula
        tipo_suelo, rango_hum, Crr, Rrod
    ]
    datos.append(fila)

# =========================
# 7. Exportar a CSV
# =========================
nombre_archivo = "datos_maquinaria.csv"

with open(nombre_archivo, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "Pnominal", "p", "T", "rho", "delta", "Pdisp",
        "",
        "Implemento", "k_base", "n", "Ancho", "Profundidad",
        "Textura", "M_textura", "Humedad(%)", "M_humedad", "Velocidad",
        "Kimpl", "Dimpl",
        "",
        "Masa_total", "Pendiente(%)", "Rpend",
        "",
        "Tipo_suelo", "Rango_humedad", "Crr", "Rrod"
    ])
    writer.writerows(datos)

print(f"Archivo CSV generado con {n_datos} datos: {nombre_archivo}")
