#!/usr/bin/env python3
"""
Script para generar reporte consolidado de métricas de pruebas unitarias UT-XXX-XXX
Extrae información sobre tiempos de respuesta, endpoints, microservicios y métricas de rendimiento
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import ast

# Mapeo de prefijos a microservicios
MICROSERVICE_MAP = {
    'CLI': 'Clientes',
    'CON': 'Contratos',
    'SOL': 'Solicitudes',
    'SER': 'Servicios',
    'MAQ': 'Maquinaria',
    'MS': 'Monitoreo',
    'SM': 'Mantenimiento',
    'PM': 'Pagos',
    'PARA': 'Parametrización',
    'GD': 'Gestión de Datos',
    'GM': 'Gestión de Mantenimiento'
}

def extract_endpoint_from_file(file_path):
    """Extrae el endpoint de un archivo de prueba"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Buscar patrones comunes de endpoints
        patterns = [
            r"endpoint\s*=\s*['\"]([^'\"]+)['\"]",
            r"endpoint\s*:\s*['\"]([^'\"]+)['\"]",
            r"['\"](/[^'\"]+)['\"]\s*#\s*endpoint",
            r"self\.endpoint\s*=\s*['\"]([^'\"]+)['\"]",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Buscar en comentarios
        endpoint_match = re.search(r"Endpoint:\s*(/[^\s]+)", content, re.IGNORECASE)
        if endpoint_match:
            return endpoint_match.group(1)
            
    except Exception as e:
        print(f"Error leyendo {file_path}: {e}")
    
    return None

def extract_response_times_from_file(file_path):
    """Extrae tiempos de respuesta medidos en el archivo"""
    response_times = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            content = ''.join(lines)
            
        # Buscar patrones de medición de tiempo más específicos
        # Patrón 1: start_time = time.time() ... end_time = time.time() ... response_time = end_time - start_time
        for i, line in enumerate(lines):
            if 'start_time' in line and 'time.time()' in line:
                # Buscar end_time en las siguientes líneas
                for j in range(i+1, min(i+20, len(lines))):
                    if 'end_time' in lines[j] and 'time.time()' in lines[j]:
                        # Buscar response_time en las siguientes líneas
                        for k in range(j+1, min(j+10, len(lines))):
                            if 'response_time' in lines[k]:
                                # Intentar extraer el valor calculado o impreso
                                response_line = lines[k]
                                # Buscar número decimal en la línea
                                time_match = re.search(r'([\d.]+)', response_line)
                                if time_match:
                                    try:
                                        val = float(time_match.group(1))
                                        if 0 < val < 100:  # Validar que sea un tiempo razonable
                                            response_times.append(val)
                                    except:
                                        pass
                        break
        
        # Buscar tiempos impresos directamente con print
        printed_times = re.findall(r'Response Time:\s*([\d.]+)', content, re.IGNORECASE)
        for pt in printed_times:
            try:
                val = float(pt)
                if 0 < val < 100:
                    response_times.append(val)
            except:
                pass
        
        # Buscar tiempos en f-strings o format
        fstring_times = re.findall(r'response_time[^}]*{([\d.]+)}', content, re.IGNORECASE)
        for ft in fstring_times:
            try:
                val = float(ft)
                if 0 < val < 100:
                    response_times.append(val)
            except:
                pass
                
        # Buscar tiempos calculados: response_time = end_time - start_time seguido de print
        calc_pattern = r'response_time\s*=\s*end_time\s*-\s*start_time'
        if re.search(calc_pattern, content, re.IGNORECASE):
            # Buscar prints después del cálculo
            after_calc = content[content.find(calc_pattern):content.find(calc_pattern)+500]
            print_times = re.findall(r'([\d.]+)\s*seconds?', after_calc, re.IGNORECASE)
            for pt in print_times:
                try:
                    val = float(pt)
                    if 0 < val < 100:
                        response_times.append(val)
                except:
                    pass
                
    except Exception as e:
        print(f"Error extrayendo tiempos de {file_path}: {e}")
    
    return response_times

def extract_test_stats_from_report(report_path):
    """Extrae estadísticas de pruebas desde reportes markdown"""
    stats = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'success_rate': 0.0,
        'response_times': []
    }
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Buscar total de pruebas
        total_match = re.search(r'Total de Pruebas[:\s]*(\d+)', content, re.IGNORECASE)
        if total_match:
            stats['total'] = int(total_match.group(1))
        
        # Buscar pruebas exitosas
        passed_match = re.search(r'Pruebas Exitosas[:\s]*(\d+)', content, re.IGNORECASE)
        if passed_match:
            stats['passed'] = int(passed_match.group(1))
        
        # Buscar pruebas fallidas
        failed_match = re.search(r'Pruebas Fallidas[:\s]*(\d+)', content, re.IGNORECASE)
        if failed_match:
            stats['failed'] = int(failed_match.group(1))
        
        # Buscar tasa de éxito
        success_match = re.search(r'Tasa de Éxito[:\s]*(\d+(?:\.\d+)?)%', content, re.IGNORECASE)
        if success_match:
            stats['success_rate'] = float(success_match.group(1))
        elif stats['total'] > 0:
            stats['success_rate'] = (stats['passed'] / stats['total']) * 100
        
        # Extraer tiempos de respuesta de reportes
        # Buscar patrones como "Tiempo de respuesta: X.XXX segundos"
        time_patterns = [
            r'Tiempo de respuesta[:\s]*([\d.]+)\s*segundos?',
            r'Response Time[:\s]*([\d.]+)\s*seconds?',
            r'response_time[:\s]*([\d.]+)',
            r'(\d+\.\d{3})\s*segundos?',
            r'(\d+\.\d{2})\s*segundos?',
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    val = float(match)
                    if 0 < val < 100:  # Validar que sea un tiempo razonable
                        stats['response_times'].append(val)
                except:
                    pass
            
    except Exception as e:
        print(f"Error leyendo reporte {report_path}: {e}")
    
    return stats

def get_microservice_from_folder(folder_name):
    """Determina el microservicio basado en el nombre de la carpeta"""
    # Extraer prefijo (ej: UT-CLI-001 -> CLI)
    match = re.match(r'UT-([A-Z]+)-\d+', folder_name)
    if match:
        prefix = match.group(1)
        return MICROSERVICE_MAP.get(prefix, prefix)
    return 'Desconocido'

def analyze_test_folder(folder_path):
    """Analiza una carpeta de pruebas y extrae métricas"""
    folder_name = folder_path.name
    microservice = get_microservice_from_folder(folder_name)
    
    metrics = {
        'test_id': folder_name,
        'microservice': microservice,
        'endpoints': [],
        'response_times': [],
        'test_stats': {'total': 0, 'passed': 0, 'failed': 0, 'success_rate': 0.0},
        'has_performance_test': False
    }
    
    # Buscar archivos de prueba
    test_files = list(folder_path.glob('test*.py'))
    report_files = list(folder_path.glob('*.md'))
    
    # Extraer endpoints de archivos de prueba
    for test_file in test_files:
        endpoint = extract_endpoint_from_file(test_file)
        if endpoint and endpoint not in metrics['endpoints']:
            metrics['endpoints'].append(endpoint)
        
        # Extraer tiempos de respuesta
        response_times = extract_response_times_from_file(test_file)
        metrics['response_times'].extend(response_times)
        if response_times:
            metrics['has_performance_test'] = True
    
    # Extraer estadísticas de reportes
    for report_file in report_files:
        stats = extract_test_stats_from_report(report_file)
        if stats['total'] > 0:
            metrics['test_stats'] = stats
        # También extraer tiempos de respuesta de reportes
        if stats['response_times']:
            metrics['response_times'].extend(stats['response_times'])
            metrics['has_performance_test'] = True
    
    # También extraer tiempos de respuesta de archivos de prueba
    for report_file in report_files:
        report_times = extract_response_times_from_file(report_file)
        if report_times:
            metrics['response_times'].extend(report_times)
            metrics['has_performance_test'] = True
    
    return metrics

def generate_report(all_metrics):
    """Genera el reporte markdown consolidado"""
    report = []
    report.append("# Reporte Consolidado de Métricas de Pruebas Unitarias")
    report.append("")
    report.append(f"**Fecha de Generación:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    report.append("")
    report.append("---")
    report.append("")
    
    # Resumen ejecutivo
    report.append("## Resumen Ejecutivo")
    report.append("")
    
    total_tests = sum(m['test_stats']['total'] for m in all_metrics if m['test_stats']['total'] > 0)
    total_passed = sum(m['test_stats']['passed'] for m in all_metrics)
    total_failed = sum(m['test_stats']['failed'] for m in all_metrics)
    total_endpoints = sum(len(m['endpoints']) for m in all_metrics)
    total_performance_tests = sum(1 for m in all_metrics if m['has_performance_test'])
    
    report.append(f"- **Total de Pruebas Unitarias Analizadas:** {len(all_metrics)}")
    report.append(f"- **Total de Pruebas Ejecutadas:** {total_tests}")
    report.append(f"- **Pruebas Exitosas:** {total_passed}")
    report.append(f"- **Pruebas Fallidas:** {total_failed}")
    report.append(f"- **Tasa de Éxito Global:** {(total_passed/total_tests*100) if total_tests > 0 else 0:.2f}%")
    report.append(f"- **Total de Endpoints Probados:** {total_endpoints}")
    report.append(f"- **Pruebas con Métricas de Rendimiento:** {total_performance_tests}")
    report.append("")
    report.append("---")
    report.append("")
    
    # Tiempo de respuesta promedio por microservicio
    report.append("## 1. Tiempo de Respuesta Promedio por Microservicio")
    report.append("")
    
    microservice_times = defaultdict(list)
    for m in all_metrics:
        if m['response_times']:
            microservice_times[m['microservice']].extend(m['response_times'])
    
    if microservice_times:
        report.append("| Microservicio | Tiempo Promedio (s) | Tiempo Mínimo (s) | Tiempo Máximo (s) | Número de Mediciones |")
        report.append("|---------------|---------------------|-------------------|-------------------|----------------------|")
        
        for microservice in sorted(microservice_times.keys()):
            times = microservice_times[microservice]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            report.append(f"| {microservice} | {avg_time:.3f} | {min_time:.3f} | {max_time:.3f} | {len(times)} |")
    else:
        report.append("*No se encontraron mediciones de tiempo de respuesta en las pruebas.*")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Consumo de CPU y RAM
    report.append("## 2. Consumo de CPU y RAM en Pruebas")
    report.append("")
    report.append("**Nota:** Las pruebas unitarias actuales no incluyen mediciones explícitas de CPU y RAM.")
    report.append("Para obtener estas métricas, se recomienda:")
    report.append("")
    report.append("1. **Usar herramientas de profiling:** `cProfile`, `memory_profiler`, `py-spy`")
    report.append("2. **Monitoreo durante ejecución:** `psutil` para medir CPU y memoria")
    report.append("3. **Integración con CI/CD:** Agregar métricas de recursos en pipelines")
    report.append("4. **Pruebas de carga:** Usar herramientas como `locust`, `k6` o `JMeter`")
    report.append("")
    report.append("**Ejemplo de implementación:**")
    report.append("```python")
    report.append("import psutil")
    report.append("import os")
    report.append("")
    report.append("process = psutil.Process(os.getpid())")
    report.append("cpu_percent = process.cpu_percent(interval=1)")
    report.append("memory_info = process.memory_info()")
    report.append("memory_mb = memory_info.rss / 1024 / 1024")
    report.append("```")
    report.append("")
    report.append("---")
    report.append("")
    
    # Número de solicitudes procesadas sin error
    report.append("## 3. Número de Solicitudes Procesadas sin Error")
    report.append("")
    
    report.append("| Microservicio | Pruebas Exitosas | Pruebas Fallidas | Tasa de Éxito (%) |")
    report.append("|---------------|------------------|------------------|-------------------|")
    
    microservice_stats = defaultdict(lambda: {'passed': 0, 'failed': 0, 'total': 0})
    for m in all_metrics:
        ms = m['microservice']
        microservice_stats[ms]['passed'] += m['test_stats']['passed']
        microservice_stats[ms]['failed'] += m['test_stats']['failed']
        microservice_stats[ms]['total'] += m['test_stats']['total']
    
    for microservice in sorted(microservice_stats.keys()):
        stats = microservice_stats[microservice]
        if stats['total'] > 0:
            success_rate = (stats['passed'] / stats['total']) * 100
            report.append(f"| {microservice} | {stats['passed']} | {stats['failed']} | {success_rate:.2f}% |")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Tabla de endpoints probados y sus tiempos
    report.append("## 4. Tabla de Endpoints Probados y sus Tiempos")
    report.append("")
    
    endpoint_data = []
    for m in all_metrics:
        for endpoint in m['endpoints']:
            times = m['response_times'] if m['response_times'] else []
            avg_time = sum(times) / len(times) if times else None
            endpoint_data.append({
                'endpoint': endpoint,
                'microservice': m['microservice'],
                'test_id': m['test_id'],
                'avg_time': avg_time,
                'times': times
            })
    
    if endpoint_data:
        report.append("| Endpoint | Microservicio | Test ID | Tiempo Promedio (s) | Tiempo Mínimo (s) | Tiempo Máximo (s) |")
        report.append("|----------|---------------|---------|---------------------|-------------------|-------------------|")
        
        for ed in sorted(endpoint_data, key=lambda x: x['endpoint']):
            endpoint = ed['endpoint']
            microservice = ed['microservice']
            test_id = ed['test_id']
            
            if ed['avg_time'] is not None:
                avg_time = ed['avg_time']
                min_time = min(ed['times'])
                max_time = max(ed['times'])
                report.append(f"| `{endpoint}` | {microservice} | {test_id} | {avg_time:.3f} | {min_time:.3f} | {max_time:.3f} |")
            else:
                report.append(f"| `{endpoint}` | {microservice} | {test_id} | *No medido* | - | - |")
    else:
        report.append("*No se encontraron endpoints con mediciones de tiempo.*")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Métricas de carga
    report.append("## 5. Métricas de Carga (Stress Test, Concurrent Users)")
    report.append("")
    report.append("**Nota:** Las pruebas unitarias actuales no incluyen pruebas de carga explícitas.")
    report.append("Para implementar pruebas de carga, se recomienda:")
    report.append("")
    report.append("### Opciones de Implementación:")
    report.append("")
    report.append("#### 1. **Locust** (Python)")
    report.append("```python")
    report.append("from locust import HttpUser, task, between")
    report.append("")
    report.append("class ApiUser(HttpUser):")
    report.append("    wait_time = between(1, 3)")
    report.append("    ")
    report.append("    @task")
    report.append("    def create_customer(self):")
    report.append("        self.client.post('/customers/create_customer/', json={...})")
    report.append("```")
    report.append("")
    report.append("#### 2. **k6** (JavaScript)")
    report.append("```javascript")
    report.append("import http from 'k6/http';")
    report.append("")
    report.append("export let options = {")
    report.append("  stages: [")
    report.append("    { duration: '30s', target: 20 },")
    report.append("    { duration: '1m', target: 50 },")
    report.append("  ],")
    report.append("};")
    report.append("")
    report.append("export default function () {")
    report.append("  http.post('http://api/customers/create_customer/', ...);")
    report.append("}")
    report.append("```")
    report.append("")
    report.append("#### 3. **JMeter** (GUI)")
    report.append("- Crear plan de prueba con Thread Groups")
    report.append("- Configurar HTTP Request Samplers")
    report.append("- Agregar listeners para métricas")
    report.append("")
    report.append("### Métricas Recomendadas a Medir:")
    report.append("")
    report.append("- **Usuarios Concurrentes:** Número máximo de usuarios simultáneos")
    report.append("- **Requests por Segundo (RPS):** Throughput del sistema")
    report.append("- **Tiempo de Respuesta bajo Carga:** P50, P95, P99")
    report.append("- **Tasa de Error:** Porcentaje de requests fallidos")
    report.append("- **CPU y Memoria:** Consumo de recursos bajo carga")
    report.append("- **Tiempo de Recuperación:** Después de remover la carga")
    report.append("")
    report.append("---")
    report.append("")
    
    # Detalle por prueba unitaria
    report.append("## 6. Detalle por Prueba Unitaria")
    report.append("")
    
    report.append("| Test ID | Microservicio | Endpoints | Pruebas Totales | Exitosas | Fallidas | Tasa Éxito | Tiempo Promedio (s) |")
    report.append("|---------|---------------|-----------|-----------------|----------|----------|------------|---------------------|")
    
    for m in sorted(all_metrics, key=lambda x: x['test_id']):
        test_id = m['test_id']
        microservice = m['microservice']
        endpoints = ', '.join(m['endpoints']) if m['endpoints'] else '*Sin endpoint*'
        total = m['test_stats']['total']
        passed = m['test_stats']['passed']
        failed = m['test_stats']['failed']
        success_rate = m['test_stats']['success_rate']
        avg_time = sum(m['response_times']) / len(m['response_times']) if m['response_times'] else None
        
        endpoints_display = endpoints[:50] + '...' if len(endpoints) > 50 else endpoints
        avg_time_display = f"{avg_time:.3f}" if avg_time else "*No medido*"
        
        report.append(f"| {test_id} | {microservice} | `{endpoints_display}` | {total} | {passed} | {failed} | {success_rate:.1f}% | {avg_time_display} |")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Recomendaciones
    report.append("## Recomendaciones")
    report.append("")
    report.append("1. **Implementar mediciones sistemáticas de tiempo de respuesta** en todas las pruebas")
    report.append("2. **Agregar métricas de CPU y RAM** usando herramientas de profiling")
    report.append("3. **Crear suite de pruebas de carga** para endpoints críticos")
    report.append("4. **Establecer SLAs** para tiempos de respuesta por microservicio")
    report.append("5. **Monitoreo continuo** en ambiente de producción")
    report.append("6. **Documentar métricas** en cada ejecución de pruebas")
    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*Reporte generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*")
    
    return '\n'.join(report)

def main():
    """Función principal"""
    test_dir = Path(__file__).parent
    all_metrics = []
    
    print("Analizando pruebas unitarias...")
    
    # Buscar todas las carpetas UT-XXX-XXX
    for folder in test_dir.iterdir():
        if folder.is_dir() and re.match(r'UT-[A-Z]+-\d+', folder.name):
            print(f"  Analizando {folder.name}...")
            metrics = analyze_test_folder(folder)
            all_metrics.append(metrics)
    
    print(f"\nTotal de pruebas analizadas: {len(all_metrics)}")
    
    # Generar reporte
    print("\nGenerando reporte...")
    report_content = generate_report(all_metrics)
    
    # Guardar reporte
    report_path = test_dir / 'REPORTE_METRICAS_CONSOLIDADO.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\nReporte generado exitosamente: {report_path}")
    print(f"Total de endpoints encontrados: {sum(len(m['endpoints']) for m in all_metrics)}")
    print(f"Total de pruebas con métricas de tiempo: {sum(1 for m in all_metrics if m['response_times'])}")

if __name__ == '__main__':
    main()

