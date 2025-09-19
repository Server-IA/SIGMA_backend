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
pendiente_range = (0, 20)       # %

# =========================
# 5. Generar datos
# =========================
n_datos = 10000
datos = []

for _ in range(n_datos):
    # ----------- PRIMERA FORMULA: Potencia disponible -----------
    Pnominal = random.uniform(*Pnominal_range)
    p = random.uniform(*p_range)
    T = random.uniform(*T_range)

    rho = p / (R * T)
    delta = rho / rho0
    Pdisp = Pnominal * delta

    # ----------- SEGUNDA FORMULA: Draft del implemento -----------
    impl = random.choice(implementos)
    k_base = impl["k_base"]
    n = impl["n"]
    nombre_impl = impl["nombre"]

    textura = random.choice(list(texturas.keys()))
    M_textura = texturas[textura]

    ancho = random.uniform(*ancho_range)
    profundidad = random.uniform(*profundidad_range)
    v = random.uniform(*velocidad_range)
    humedad = random.uniform(*humedad_range)
    M_humedad = humedad_factor(humedad)

    Kimpl = (
        k_base
        * M_textura
        * M_humedad
        * (profundidad / 0.20) ** n
        * (1 + alpha * (v - 5))
    )

    Dimpl = Kimpl * ancho * profundidad

    # ----------- TERCERA FORMULA: Resistencia por pendiente -----------
    masa_total = random.uniform(*masa_range)
    pendiente = random.uniform(*pendiente_range)

    Rpend = masa_total * g * (pendiente / 100)

    # ----------- UNIR TODO EN UNA SOLA FILA -----------
    fila = [
        # Datos primera fórmula
        Pnominal, p, T, rho, delta, Pdisp,

        # Columna vacía
        "",

        # Datos segunda fórmula
        nombre_impl, k_base, n, ancho, profundidad,
        textura, M_textura, humedad, M_humedad, v,
        Kimpl, Dimpl,

        # Columna vacía
        "",

        # Datos tercera fórmula
        masa_total, pendiente, Rpend
    ]
    datos.append(fila)

# =========================
# 6. Exportar a CSV
# =========================
nombre_archivo = "datos_maquinaria.csv"

with open(nombre_archivo, mode="w", newline="") as file:
    writer = csv.writer(file)
    # Encabezados
    writer.writerow([
        "Pnominal", "p", "T", "rho", "delta", "Pdisp",
        "",
        "Implemento", "k_base", "n", "Ancho", "Profundidad",
        "Textura", "M_textura", "Humedad(%)", "M_humedad", "Velocidad",
        "Kimpl", "Dimpl",
        "",
        "Masa_total", "Pendiente(%)", "Rpend"
    ])
    writer.writerows(datos)

print(f"Archivo CSV generado con {n_datos} datos: {nombre_archivo}")
