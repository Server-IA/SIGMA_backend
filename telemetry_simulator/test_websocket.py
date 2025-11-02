"""
Script de prueba para el servicio de telemetría WebSocket
"""
import asyncio
import json
import websockets
import sys


async def test_telemetry_websocket():
    """
    Prueba la conexión al WebSocket de telemetría
    """
    uri = "ws://localhost:8003/ws/telemetria"
    
    print("🔌 Conectando a WebSocket...")
    print(f"📍 URI: {uri}")
    print("-" * 60)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Conectado exitosamente!")
            print("📡 Esperando datos de telemetría...")
            print("-" * 60)
            
            # Recibir 5 mensajes para la prueba
            for i in range(5):
                try:
                    data = await websocket.recv()
                    telemetry = json.loads(data)
                    
                    print(f"\n🔔 Mensaje #{i + 1} recibido:")
                    print(f"📱 IMEI: {telemetry.get('imei', 'N/A')}")
                    print(f"⏰ Timestamp: {telemetry['timestamp']}")
                    print(f"🚗 Velocidad: {telemetry['data']['speed']} km/h")
                    print(f"🔋 Ignición: {'ON' if telemetry['data']['ignition_status'] else 'OFF'}")
                    print(f"🚦 Movimiento: {'SI' if telemetry['data']['movement_status'] else 'NO'}")
                    print(f"🔧 RPM: {telemetry['data']['rpm']}")
                    print(f"🌡️ Temp Motor: {telemetry['data']['engine_temp']}°C")
                    print(f"⛽ Combustible: {telemetry['data']['fuel_level']}%")
                    print(f"📍 GPS: {telemetry['data']['gps_location']}")
                    
                    if telemetry['data']['obd_faults']:
                        print(f"⚠️ Fallas: {telemetry['data']['obd_faults']}")
                    else:
                        print("✅ Sin fallas OBD")
                    
                    print("-" * 60)
                    
                except Exception as e:
                    print(f"❌ Error recibiendo mensaje: {str(e)}")
                    break
            
            print("\n✅ Prueba completada exitosamente!")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Error: No se pudo conectar al servidor")
        print("💡 Asegúrate de que el servicio esté corriendo con: docker-compose up")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PRUEBA DEL SERVICIO DE TELEMETRÍA")
    print("=" * 60)
    asyncio.run(test_telemetry_websocket())

