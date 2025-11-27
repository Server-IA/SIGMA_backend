"""
Decodificador CODEC 8E para buffers FMC150
Usa nombres de parámetros desde la base de datos
"""
import binascii
import struct
from datetime import datetime, timedelta
import logging

from fmc150_decoder.db_service import get_parameter_name

logger = logging.getLogger(__name__)

PRIORITY_NAMES = {0: "Low", 1: "High", 2: "Panic"}

def _to_signed_32(v: int) -> int:
    return v - 0x100000000 if v & 0x80000000 else v

def decode_gps_coordinate(value):
    """Decodifica coordenada GPS desde entero signed 32 bits / 10^7"""
    return _to_signed_32(value) / 10000000.0

def decode_timestamp(ms):
    """Decodifica timestamp desde milisegundos Unix"""
    return str(datetime(1970, 1, 1) + timedelta(milliseconds=ms))

def decode_codec8e(hex_data, imei=None):
    """
    Decodifica buffer hexadecimal CODEC 8E del FMC150
    
    Args:
        hex_data: String hexadecimal del buffer
        imei: IMEI del dispositivo (opcional)
    
    Returns:
        list: Lista de registros decodificados (dict)
    """
    data = bytes.fromhex(hex_data)
    offset = 0
    
    def read(fmt):
        nonlocal offset
        size = struct.calcsize(fmt)
        val = struct.unpack(fmt, data[offset:offset+size])
        offset += size
        return val if len(val) > 1 else val[0]
    
    # Preamble, length, codec, num recs
    preamble = read('>I')
    data_length = read('>I')
    codec_id = read('>B')
    num_records = read('>B')
    
    registros = []
    for _ in range(num_records):
        reg = {}
        ts = read('>Q')
        reg['timestamp'] = decode_timestamp(ts)
        reg['priority'] = read('>B')
        reg['gps'] = {
            'longitude': decode_gps_coordinate(read('>i')),
            'latitude': decode_gps_coordinate(read('>i')),
            'altitude': read('>h'),
            'angle': read('>H'),
            'satellites': read('>B'),
            'speed': read('>H')
        }
        
        # IO Elements (solo IDs y valores principales)
        event_io_id = read('>H')
        total_io = read('>H')
        
        io = {}
        
        # Leer elementos de 1 byte
        n1 = read('>H')
        for _ in range(n1):
            io_id = read('>H')
            io_val = read('>B')
            io[get_parameter_name(io_id)] = io_val
        
        # Leer elementos de 2 bytes
        n2 = read('>H')
        for _ in range(n2):
            io_id = read('>H')
            io_val = read('>H')
            io[get_parameter_name(io_id)] = io_val
        
        # Leer elementos de 4 bytes
        n4 = read('>H')
        for _ in range(n4):
            io_id = read('>H')
            io_val = read('>I')
            io[get_parameter_name(io_id)] = io_val
        
        # Leer elementos de 8 bytes
        n8 = read('>H')
        for _ in range(n8):
            io_id = read('>H')
            io_val = read('>Q')
            io[get_parameter_name(io_id)] = io_val
        
        # Leer elementos de longitud variable
        nx = read('>H')
        for _ in range(nx):
            io_id = read('>H')
            io_len = read('>H')
            io_val = data[offset:offset+io_len]
            offset += io_len
            io[get_parameter_name(io_id)] = binascii.hexlify(io_val).decode()
        
        reg['io'] = io
        if imei:
            reg['imei'] = imei
        registros.append(reg)
    
    return registros

def hex_dump(data, bytes_per_line=16):
    """Genera un hex dump legible de los datos"""
    lines = []
    for i in range(0, len(data), bytes_per_line):
        chunk = data[i:i + bytes_per_line]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f'{i:04X}  {hex_part:<48}  {ascii_part}')
    return '\n'.join(lines)

