#!/usr/bin/env python
"""
Script de ejecución para la suite WS-MS-002
Ejecuta los tests de WebSocket con configuración optimizada
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Ejecuta la suite de tests WS-MS-002"""
    
    # Directorio de tests
    test_dir = Path(__file__).parent
    
    # Argumentos base de pytest
    pytest_args = [
        "pytest",
        str(test_dir),
        "-v",  # Verbose
        "--tb=short",  # Traceback corto
        "--log-cli-level=INFO",  # Logs en consola
        "-p", "no:warnings",  # Sin warnings
        "--ds=machpaymanager.settings",  # Django settings
    ]
    
    # Parsear argumentos adicionales
    if len(sys.argv) > 1:
        if sys.argv[1] == "--all":
            # Ejecutar todos incluyendo skipped
            pytest_args.append("--run-skipped")
        elif sys.argv[1] == "--security":
            # Solo tests de seguridad
            pytest_args.extend(["-m", "security"])
        elif sys.argv[1] == "--performance":
            # Solo tests de performance
            pytest_args.extend(["-m", "performance"])
        elif sys.argv[1] == "--quick":
            # Solo tests rápidos (sin skipped)
            pytest_args.append("--ignore-skip")
        elif sys.argv[1].startswith("test_"):
            # Archivo específico
            pytest_args = ["pytest", str(test_dir / sys.argv[1]), "-v"]
        else:
            print("Uso: python run_tests.py [--all|--security|--performance|--quick|test_XXX.py]")
            sys.exit(1)
    
    # Ejecutar pytest
    print(f"Ejecutando: {' '.join(pytest_args)}")
    print("-" * 80)
    
    result = subprocess.run(pytest_args)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
