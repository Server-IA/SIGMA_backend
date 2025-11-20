#!/usr/bin/env python3
"""
Script para ejecutar pruebas unitarias UT-XXX-XXX en Docker y capturar métricas en tiempo real
Incluye medición de CPU, RAM, tiempos de respuesta y generación de reporte consolidado
"""

import subprocess
import json
import re
import time
import threading
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

# Configuración
DOCKER_CONTAINER = "machpay_backend"
TEST_DIR = Path(__file__).parent

class DockerStatsMonitor:
    """Monitor de estadísticas de Docker en tiempo real"""
    
    def __init__(self, container_name):
        self.container_name = container_name
        self.stats = []
        self.running = False
        self.thread = None
        
    def start(self):
        """Inicia el monitoreo en un thread separado"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Detiene el monitoreo"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _monitor_loop(self):
        """Loop de monitoreo que captura estadísticas de Docker"""
        try:
            cmd = ["docker", "stats", self.container_name, "--no-stream", "--format", 
                   "{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}"]
            
            while self.running:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if result.returncode == 0 and result.stdout.strip():
                        # Parsear: "0.50%,100MiB / 2GiB,5.00%"
                        parts = result.stdout.strip().split(',')
                        if len(parts) >= 3:
                            cpu_percent = float(parts[0].replace('%', ''))
                            mem_usage = parts[1].strip()
                            mem_percent = float(parts[2].replace('%', ''))
                            
                            # Extraer memoria usada y total
                            mem_match = re.match(r'(\d+(?:\.\d+)?)(\w+)\s*/\s*(\d+(?:\.\d+)?)(\w+)', mem_usage)
                            if mem_match:
                                mem_used_val = float(mem_match.group(1))
                                mem_used_unit = mem_match.group(2)
                                mem_total_val = float(mem_match.group(3))
                                mem_total_unit = mem_match.group(4)
                                
                                # Convertir a MB
                                mem_used_mb = self._to_mb(mem_used_val, mem_used_unit)
                                mem_total_mb = self._to_mb(mem_total_val, mem_total_unit)
                                
                                self.stats.append({
                                    'timestamp': time.time(),
                                    'cpu_percent': cpu_percent,
                                    'memory_used_mb': mem_used_mb,
                                    'memory_total_mb': mem_total_mb,
                                    'memory_percent': mem_percent
                                })
                except Exception as e:
                    print(f"Error capturando stats: {e}", file=sys.stderr)
                
                time.sleep(1)  # Capturar cada 1 segundo
        except Exception as e:
            print(f"Error en monitor loop: {e}", file=sys.stderr)
    
    def _to_mb(self, value, unit):
        """Convierte unidades de memoria a MB"""
        unit = unit.upper()
        if unit == 'KB':
            return value / 1024
        elif unit == 'MB':
            return value
        elif unit == 'GB':
            return value * 1024
        elif unit == 'B':
            return value / (1024 * 1024)
        return value
    
    def get_summary(self):
        """Retorna resumen de estadísticas"""
        if not self.stats:
            return {
                'avg_cpu': 0,
                'max_cpu': 0,
                'avg_memory_mb': 0,
                'max_memory_mb': 0,
                'samples': 0
            }
        
        cpu_values = [s['cpu_percent'] for s in self.stats]
        memory_values = [s['memory_used_mb'] for s in self.stats]
        
        return {
            'avg_cpu': sum(cpu_values) / len(cpu_values),
            'max_cpu': max(cpu_values),
            'avg_memory_mb': sum(memory_values) / len(memory_values),
            'max_memory_mb': max(memory_values),
            'samples': len(self.stats)
        }

def run_test_in_docker(test_path):
    """Ejecuta una prueba en Docker y captura métricas"""
    print(f"\n{'='*80}")
    print(f"Ejecutando: {test_path}")
    print(f"{'='*80}")
    
    # Iniciar monitor de estadísticas
    monitor = DockerStatsMonitor(DOCKER_CONTAINER)
    monitor.start()
    
    try:
        # Comando para ejecutar pytest en Docker
        cmd = [
            "docker", "exec", DOCKER_CONTAINER,
            "python", "-m", "pytest", str(test_path),
            "-v", "--tb=short", "-q"
        ]
        
        # Ejecutar prueba y medir tiempo
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Detener monitor
        monitor.stop()
        
        # Analizar salida de pytest
        output = result.stdout + result.stderr
        
        # Extraer estadísticas de pytest
        passed = len(re.findall(r'PASSED', output))
        failed = len(re.findall(r'FAILED', output))
        skipped = len(re.findall(r'SKIPPED', output))
        error = len(re.findall(r'ERROR', output))
        
        # Buscar tiempos de respuesta en la salida
        response_times = []
        time_matches = re.findall(r'(\d+\.\d{3})\s*seconds?', output, re.IGNORECASE)
        for tm in time_matches:
            try:
                response_times.append(float(tm))
            except:
                pass
        
        # Obtener resumen de recursos
        resource_summary = monitor.get_summary()
        
        return {
            'test_path': str(test_path),
            'execution_time': execution_time,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'error': error,
            'total': passed + failed + skipped + error,
            'response_times': response_times,
            'cpu_avg': resource_summary['avg_cpu'],
            'cpu_max': resource_summary['max_cpu'],
            'memory_avg_mb': resource_summary['avg_memory_mb'],
            'memory_max_mb': resource_summary['max_memory_mb'],
            'return_code': result.returncode,
            'output': output[:1000]  # Primeros 1000 caracteres
        }
        
    except subprocess.TimeoutExpired:
        monitor.stop()
        return {
            'test_path': str(test_path),
            'execution_time': 300,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'error': 1,
            'total': 0,
            'response_times': [],
            'cpu_avg': 0,
            'cpu_max': 0,
            'memory_avg_mb': 0,
            'memory_max_mb': 0,
            'return_code': -1,
            'output': 'TIMEOUT'
        }
    except Exception as e:
        monitor.stop()
        return {
            'test_path': str(test_path),
            'execution_time': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'error': 1,
            'total': 0,
            'response_times': [],
            'cpu_avg': 0,
            'cpu_max': 0,
            'memory_avg_mb': 0,
            'memory_max_mb': 0,
            'return_code': -1,
            'output': str(e)
        }

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

def generate_metrics_report(test_results):
    """Genera reporte de métricas consolidado"""
    report = []
    report.append("# Reporte Consolidado de Métricas de Pruebas Unitarias")
    report.append("")
    report.append(f"**Fecha de Generación:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    report.append(f"**Ejecutado en:** Docker Container ({DOCKER_CONTAINER})")
    report.append("")
    report.append("---")
    report.append("")
    
    # Resumen ejecutivo
    total_tests = sum(r['total'] for r in test_results)
    total_passed = sum(r['passed'] for r in test_results)
    total_failed = sum(r['failed'] for r in test_results)
    total_execution_time = sum(r['execution_time'] for r in test_results)
    
    report.append("## Resumen Ejecutivo")
    report.append("")
    report.append(f"- **Total de Pruebas Ejecutadas:** {len(test_results)}")
    report.append(f"- **Total de Tests:** {total_tests}")
    report.append(f"- **Tests Exitosos:** {total_passed}")
    report.append(f"- **Tests Fallidos:** {total_failed}")
    report.append(f"- **Tasa de Éxito:** {(total_passed/total_tests*100) if total_tests > 0 else 0:.2f}%")
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
            if result['response_times']:
                microservice_times[microservice].extend(result['response_times'])
            # También usar tiempo de ejecución como métrica
            microservice_times[microservice].append(result['execution_time'])
    
    if microservice_times:
        report.append("| Microservicio | Tiempo Promedio (s) | Tiempo Mínimo (s) | Tiempo Máximo (s) | Mediciones |")
        report.append("|---------------|---------------------|-------------------|-------------------|------------|")
        
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
    
    # Consumo de CPU y RAM
    report.append("## 2. Consumo de CPU y RAM en Pruebas")
    report.append("")
    
    # Agrupar por microservicio
    microservice_resources = defaultdict(lambda: {'cpu': [], 'memory': []})
    
    for result in test_results:
        test_id = Path(result['test_path']).parent.name
        match = re.match(r'UT-([A-Z]+)-\d+', test_id)
        if match:
            prefix = match.group(1)
            microservice = microservice_map.get(prefix, prefix)
            if result['cpu_avg'] > 0:
                microservice_resources[microservice]['cpu'].append(result['cpu_avg'])
            if result['memory_avg_mb'] > 0:
                microservice_resources[microservice]['memory'].append(result['memory_avg_mb'])
    
    if any(microservice_resources.values()):
        report.append("| Microservicio | CPU Promedio (%) | CPU Máximo (%) | RAM Promedio (MB) | RAM Máximo (MB) |")
        report.append("|---------------|------------------|----------------|-------------------|-----------------|")
        
        for microservice in sorted(microservice_resources.keys()):
            cpu_vals = microservice_resources[microservice]['cpu']
            mem_vals = microservice_resources[microservice]['memory']
            
            if cpu_vals and mem_vals:
                cpu_avg = sum(cpu_vals) / len(cpu_vals)
                cpu_max = max(cpu_vals)
                mem_avg = sum(mem_vals) / len(mem_vals)
                mem_max = max(mem_vals)
                
                report.append(f"| {microservice} | {cpu_avg:.2f} | {cpu_max:.2f} | {mem_avg:.2f} | {mem_max:.2f} |")
    else:
        report.append("*No se capturaron métricas de CPU/RAM durante la ejecución.*")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Número de solicitudes procesadas sin error
    report.append("## 3. Número de Solicitudes Procesadas sin Error")
    report.append("")
    
    report.append("| Microservicio | Tests Exitosos | Tests Fallidos | Tasa de Éxito (%) |")
    report.append("|---------------|----------------|----------------|-------------------|")
    
    microservice_stats = defaultdict(lambda: {'passed': 0, 'failed': 0, 'total': 0})
    for result in test_results:
        test_id = Path(result['test_path']).parent.name
        match = re.match(r'UT-([A-Z]+)-\d+', test_id)
        if match:
            prefix = match.group(1)
            microservice = microservice_map.get(prefix, prefix)
            microservice_stats[microservice]['passed'] += result['passed']
            microservice_stats[microservice]['failed'] += result['failed']
            microservice_stats[microservice]['total'] += result['total']
    
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
    report.append("| Test ID | Microservicio | Tiempo Ejecución (s) | Tests Pasados | Tests Fallidos | CPU Promedio (%) | RAM Promedio (MB) |")
    report.append("|---------|---------------|---------------------|---------------|----------------|------------------|-------------------|")
    
    for result in sorted(test_results, key=lambda x: Path(x['test_path']).parent.name):
        test_id = Path(result['test_path']).parent.name
        match = re.match(r'UT-([A-Z]+)-\d+', test_id)
        microservice = microservice_map.get(match.group(1), match.group(1)) if match else 'Desconocido'
        
        report.append(f"| {test_id} | {microservice} | {result['execution_time']:.2f} | {result['passed']} | {result['failed']} | {result['cpu_avg']:.2f} | {result['memory_avg_mb']:.2f} |")
    
    report.append("")
    report.append("---")
    report.append("")
    
    # Métricas de carga
    report.append("## 5. Métricas de Carga (Stress Test, Concurrent Users)")
    report.append("")
    report.append("**Nota:** Las pruebas unitarias actuales se ejecutan de forma secuencial.")
    report.append("Para pruebas de carga concurrente, se recomienda usar herramientas especializadas:")
    report.append("")
    report.append("- **Locust**: Para pruebas de carga con Python")
    report.append("- **k6**: Para pruebas de carga con JavaScript")
    report.append("- **JMeter**: Para pruebas de carga con GUI")
    report.append("")
    report.append("**Métricas capturadas durante ejecución:**")
    report.append(f"- Tiempo total de ejecución: {total_execution_time:.2f} segundos")
    report.append(f"- Promedio de CPU durante pruebas: {sum(r['cpu_avg'] for r in test_results)/len(test_results) if test_results else 0:.2f}%")
    report.append(f"- Máximo de CPU durante pruebas: {max((r['cpu_max'] for r in test_results), default=0):.2f}%")
    report.append(f"- Promedio de RAM durante pruebas: {sum(r['memory_avg_mb'] for r in test_results)/len(test_results) if test_results else 0:.2f} MB")
    report.append(f"- Máximo de RAM durante pruebas: {max((r['memory_max_mb'] for r in test_results), default=0):.2f} MB")
    report.append("")
    report.append("---")
    report.append("")
    
    report.append(f"*Reporte generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*")
    
    return '\n'.join(report)

def main():
    """Función principal"""
    print("="*80)
    print("Ejecutando Pruebas Unitarias con Captura de Métricas")
    print("="*80)
    print(f"Contenedor Docker: {DOCKER_CONTAINER}")
    print(f"Directorio de pruebas: {TEST_DIR}")
    print("")
    
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
    
    # Preguntar si ejecutar todas o solo algunas
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            selected_tests = test_folders
        else:
            # Filtrar por patrón
            pattern = sys.argv[1]
            selected_tests = [(name, path) for name, path in test_folders if pattern in name]
    else:
        # Por defecto, ejecutar solo las primeras 5 para prueba
        print("NOTA: Ejecutando solo las primeras 5 pruebas como demostración.")
        print("Usa --all para ejecutar todas las pruebas.")
        print("")
        selected_tests = test_folders[:5]
    
    # Ejecutar pruebas y capturar métricas
    test_results = []
    for i, (folder_name, test_path) in enumerate(selected_tests, 1):
        print(f"\n[{i}/{len(selected_tests)}] Procesando {folder_name}...")
        result = run_test_in_docker(test_path)
        test_results.append(result)
        
        # Resumen rápido
        print(f"  [OK] Ejecutado en {result['execution_time']:.2f}s")
        print(f"  [OK] Tests: {result['passed']} pasados, {result['failed']} fallidos")
        if result['cpu_avg'] > 0:
            print(f"  [OK] CPU: {result['cpu_avg']:.2f}% (max: {result['cpu_max']:.2f}%)")
        if result['memory_avg_mb'] > 0:
            print(f"  [OK] RAM: {result['memory_avg_mb']:.2f} MB (max: {result['memory_max_mb']:.2f} MB)")
    
    # Generar reporte
    print("\n" + "="*80)
    print("Generando reporte consolidado...")
    print("="*80)
    
    report_content = generate_metrics_report(test_results)
    
    # Guardar reporte
    report_path = TEST_DIR / 'REPORTE_METRICAS_EJECUCION_REAL.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n[OK] Reporte generado: {report_path}")
    print(f"[OK] Total de pruebas ejecutadas: {len(test_results)}")
    print(f"[OK] Tests exitosos: {sum(r['passed'] for r in test_results)}")
    print(f"[OK] Tests fallidos: {sum(r['failed'] for r in test_results)}")

if __name__ == '__main__':
    main()
