#!/usr/bin/env python3
"""
Script optimizado para ejecutar todas las pruebas UT-XXX-XXX rápidamente
"""

import subprocess
import re
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

# Configuración
DOCKER_CONTAINER = "machpay_backend"
TEST_DIR = Path(__file__).parent

def find_ut_test_folders():
    """Encuentra todas las carpetas de pruebas UT-XXX-XXX"""
    test_folders = []
    for folder in TEST_DIR.iterdir():
        if folder.is_dir() and re.match(r'UT-[A-Z]+-\d+', folder.name):
            # Buscar archivo de prueba principal
            test_files = list(folder.glob('test*.py'))
            if test_files:
                test_folders.append((folder.name, test_files[0]))
    return sorted(test_folders)

def run_test_simple(test_path):
    """Ejecuta una prueba de manera simple y rápida"""
    print(f"Ejecutando: {Path(test_path).parent.name}")
    
    try:
        # Comando para ejecutar pytest en Docker con ruta correcta
        relative_path = f"test/{Path(test_path).parent.name}/{Path(test_path).name}"
        cmd = [
            "docker", "exec", DOCKER_CONTAINER,
            "python", "-m", "pytest", relative_path,
            "-v", "--tb=short", "-q"
        ]
        
        # Ejecutar prueba y medir tiempo
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Analizar salida de pytest
        output = result.stdout + result.stderr
        
        # Extraer estadísticas de pytest
        passed = len(re.findall(r'PASSED', output))
        failed = len(re.findall(r'FAILED', output))
        skipped = len(re.findall(r'SKIPPED', output))
        error = len(re.findall(r'ERROR', output))
        
        return {
            'test_path': str(test_path),
            'execution_time': execution_time,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'error': error,
            'total': passed + failed + skipped + error,
            'return_code': result.returncode,
            'success': result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        return {
            'test_path': str(test_path),
            'execution_time': 60,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'error': 1,
            'total': 0,
            'return_code': -1,
            'success': False
        }
    except Exception as e:
        return {
            'test_path': str(test_path),
            'execution_time': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'error': 1,
            'total': 0,
            'return_code': -1,
            'success': False
        }

def generate_complete_report(test_results):
    """Genera reporte completo de métricas"""
    report = []
    report.append("# Reporte Completo de Métricas de Pruebas Unitarias UT-XXX-XXX")
    report.append("")
    report.append(f"**Fecha de Generación:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    report.append(f"**Ejecutado en:** Docker Container ({DOCKER_CONTAINER})")
    report.append(f"**Total de Pruebas Analizadas:** {len(test_results)}")
    report.append("")
    report.append("---")
    report.append("")
    
    # Resumen ejecutivo
    total_tests = sum(r['total'] for r in test_results)
    total_passed = sum(r['passed'] for r in test_results)
    total_failed = sum(r['failed'] for r in test_results)
    total_execution_time = sum(r['execution_time'] for r in test_results)
    successful_executions = sum(1 for r in test_results if r['success'])
    
    report.append("## Resumen Ejecutivo")
    report.append("")
    report.append(f"- **Total de Suites de Pruebas:** {len(test_results)}")
    report.append(f"- **Suites Ejecutadas Exitosamente:** {successful_executions}")
    report.append(f"- **Total de Tests Individuales:** {total_tests}")
    report.append(f"- **Tests Exitosos:** {total_passed}")
    report.append(f"- **Tests Fallidos:** {total_failed}")
    report.append(f"- **Tasa de Éxito de Suites:** {(successful_executions/len(test_results)*100) if test_results else 0:.2f}%")
    report.append(f"- **Tasa de Éxito de Tests:** {(total_passed/total_tests*100) if total_tests > 0 else 0:.2f}%")
    report.append(f"- **Tiempo Total de Ejecución:** {total_execution_time:.2f} segundos")
    report.append("")
    report.append("---")
    report.append("")
    
    # Tiempo de respuesta promedio por microservicio
    report.append("## 1. Tiempo de Respuesta Promedio por Microservicio")
    report.append("")
    
    microservice_times = defaultdict(list)
    microservice_map = {
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
    
    for result in test_results:
        test_id = Path(result['test_path']).parent.name
        match = re.match(r'UT-([A-Z]+)-\d+', test_id)
        if match:
            prefix = match.group(1)
            microservice = microservice_map.get(prefix, prefix)
            microservice_times[microservice].append(result['execution_time'])
    
    if microservice_times:
        report.append("| Microservicio | Tiempo Promedio (s) | Tiempo Mínimo (s) | Tiempo Máximo (s) | Pruebas |")
        report.append("|---------------|---------------------|-------------------|-------------------|---------|")
        
        for microservice in sorted(microservice_times.keys()):
            times = microservice_times[microservice]
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            report.append(f"| {microservice} | {avg_time:.3f} | {min_time:.3f} | {max_time:.3f} | {len(times)} |")
    else:
        report.append("*No se encontraron mediciones de tiempo.*")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Número de solicitudes procesadas sin error
    report.append("## 2. Número de Solicitudes Procesadas sin Error")
    report.append("")
    
    report.append("| Microservicio | Suites Exitosas | Suites Fallidas | Tests Pasados | Tests Fallidos | Tasa de Éxito (%) |")
    report.append("|---------------|-----------------|-----------------|---------------|----------------|-------------------|")
    
    microservice_stats = defaultdict(lambda: {'suites_ok': 0, 'suites_fail': 0, 'passed': 0, 'failed': 0, 'total': 0})
    for result in test_results:
        test_id = Path(result['test_path']).parent.name
        match = re.match(r'UT-([A-Z]+)-\d+', test_id)
        if match:
            prefix = match.group(1)
            microservice = microservice_map.get(prefix, prefix)
            if result['success']:
                microservice_stats[microservice]['suites_ok'] += 1
            else:
                microservice_stats[microservice]['suites_fail'] += 1
            microservice_stats[microservice]['passed'] += result['passed']
            microservice_stats[microservice]['failed'] += result['failed']
            microservice_stats[microservice]['total'] += result['total']
    
    for microservice in sorted(microservice_stats.keys()):
        stats = microservice_stats[microservice]
        total_suites = stats['suites_ok'] + stats['suites_fail']
        suite_success_rate = (stats['suites_ok'] / total_suites * 100) if total_suites > 0 else 0
        report.append(f"| {microservice} | {stats['suites_ok']} | {stats['suites_fail']} | {stats['passed']} | {stats['failed']} | {suite_success_rate:.2f}% |")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Tabla de endpoints probados y sus tiempos
    report.append("## 3. Tabla de Endpoints Probados y sus Tiempos")
    report.append("")
    report.append("| Test ID | Microservicio | Tiempo Ejecución (s) | Tests Pasados | Tests Fallidos | Estado |")
    report.append("|---------|---------------|---------------------|---------------|----------------|--------|")
    
    for result in sorted(test_results, key=lambda x: Path(x['test_path']).parent.name):
        test_id = Path(result['test_path']).parent.name
        match = re.match(r'UT-([A-Z]+)-\d+', test_id)
        microservice = microservice_map.get(match.group(1), match.group(1)) if match else 'Desconocido'
        status = "OK" if result['success'] else "ERROR"
        
        report.append(f"| {test_id} | {microservice} | {result['execution_time']:.2f} | {result['passed']} | {result['failed']} | {status} |")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Métricas de carga estimadas
    report.append("## 4. Métricas de Carga Estimadas")
    report.append("")
    report.append("**Basado en la ejecución secuencial de pruebas unitarias:**")
    report.append("")
    report.append(f"- **Tiempo total de ejecución:** {total_execution_time:.2f} segundos")
    report.append(f"- **Tiempo promedio por prueba:** {total_execution_time/len(test_results) if test_results else 0:.2f} segundos")
    report.append(f"- **Throughput estimado:** {len(test_results)/total_execution_time if total_execution_time > 0 else 0:.2f} pruebas/segundo")
    report.append(f"- **Capacidad estimada por minuto:** {(len(test_results)/total_execution_time)*60 if total_execution_time > 0 else 0:.0f} pruebas/minuto")
    report.append("")
    report.append("**Recomendaciones para pruebas de carga:**")
    report.append("- Usar herramientas especializadas como Locust, k6 o JMeter")
    report.append("- Implementar pruebas de carga específicas para endpoints críticos")
    report.append("- Monitorear CPU y RAM durante pruebas de carga reales")
    report.append("")
    report.append("---")
    report.append("")
    
    # Análisis por microservicio
    report.append("## 5. Análisis Detallado por Microservicio")
    report.append("")
    
    for microservice in sorted(microservice_stats.keys()):
        stats = microservice_stats[microservice]
        times = microservice_times[microservice]
        
        report.append(f"### {microservice}")
        report.append("")
        report.append(f"- **Suites de prueba:** {stats['suites_ok'] + stats['suites_fail']}")
        report.append(f"- **Suites exitosas:** {stats['suites_ok']}")
        report.append(f"- **Tests individuales:** {stats['total']}")
        report.append(f"- **Tiempo promedio:** {sum(times)/len(times) if times else 0:.2f}s")
        report.append(f"- **Tiempo total:** {sum(times):.2f}s")
        report.append("")
    
    report.append("---")
    report.append("")
    report.append(f"*Reporte generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*")
    
    return '\n'.join(report)

def main():
    """Función principal"""
    print("="*80)
    print("Ejecutando TODAS las Pruebas Unitarias UT-XXX-XXX")
    print("="*80)
    
    # Verificar que el contenedor esté corriendo
    check_cmd = ["docker", "ps", "--filter", f"name={DOCKER_CONTAINER}", "--format", "{{.Names}}"]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    if DOCKER_CONTAINER not in result.stdout:
        print(f"ERROR: El contenedor {DOCKER_CONTAINER} no está corriendo.")
        print("Por favor, ejecuta: docker-compose up -d")
        sys.exit(1)
    
    # Encontrar todas las pruebas UT-XXX-XXX
    test_folders = find_ut_test_folders()
    print(f"Encontradas {len(test_folders)} pruebas unitarias")
    print("")
    
    # Ejecutar todas las pruebas
    test_results = []
    for i, (folder_name, test_path) in enumerate(test_folders, 1):
        print(f"[{i}/{len(test_folders)}] {folder_name}...", end=" ")
        result = run_test_simple(test_path)
        test_results.append(result)
        
        status = "OK" if result['success'] else "ERROR"
        print(f"{status} ({result['execution_time']:.2f}s)")
    
    # Generar reporte
    print("\n" + "="*80)
    print("Generando reporte completo...")
    print("="*80)
    
    report_content = generate_complete_report(test_results)
    
    # Guardar reporte
    report_path = TEST_DIR / 'REPORTE_METRICAS_COMPLETO.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n[OK] Reporte completo generado: {report_path}")
    print(f"[OK] Total de pruebas ejecutadas: {len(test_results)}")
    print(f"[OK] Suites exitosas: {sum(1 for r in test_results if r['success'])}")
    print(f"[OK] Tests individuales exitosos: {sum(r['passed'] for r in test_results)}")
    print(f"[OK] Tests individuales fallidos: {sum(r['failed'] for r in test_results)}")

if __name__ == '__main__':
    main()
