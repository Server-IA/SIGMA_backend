import re
import math
from typing import Dict, Tuple

class ContrastValidator:
    def __init__(self):
        self.wcag_aa_normal = 4.5
        self.wcag_aa_large = 3.0
        self.wcag_aaa_normal = 7.0
        self.wcag_aaa_large = 4.5

    def validate_hex_color(self, color: str) -> bool:
        if not color:
            return False
        return bool(re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color))

    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c + c for c in hex_color])
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)

    def rgb_to_srgb(self, rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        r, g, b = rgb
        def to_srgb(value):
            value = value / 255.0
            if value <= 0.03928:
                return value / 12.92
            return math.pow((value + 0.055) / 1.055, 2.4)
        return (to_srgb(r), to_srgb(g), to_srgb(b))

    def calculate_luminance(self, srgb: Tuple[float, float, float]) -> float:
        r, g, b = srgb
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        if not self.validate_hex_color(color1) or not self.validate_hex_color(color2):
            raise ValueError("Colores deben estar en formato hexadecimal válido")
        rgb1 = self.hex_to_rgb(color1)
        rgb2 = self.hex_to_rgb(color2)
        srgb1 = self.rgb_to_srgb(rgb1)
        srgb2 = self.rgb_to_srgb(rgb2)
        lum1 = self.calculate_luminance(srgb1)
        lum2 = self.calculate_luminance(srgb2)
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)

    def validate_contrast(self, background_color: str, text_color: str, level: str = 'AA', text_size: str = 'normal') -> Dict:
        if not self.validate_hex_color(background_color):
            return {'valid': False, 'error': f"Color de fondo '{background_color}' no tiene formato hexadecimal válido"}
        if not self.validate_hex_color(text_color):
            return {'valid': False, 'error': f"Color de texto '{text_color}' no tiene formato hexadecimal válido"}
        ratio = self.calculate_contrast_ratio(background_color, text_color)
        if level == 'AA':
            threshold = self.wcag_aa_large if text_size == 'large' else self.wcag_aa_normal
        else:
            threshold = self.wcag_aaa_large if text_size == 'large' else self.wcag_aaa_normal
        is_valid = ratio >= threshold
        return {
            'valid': is_valid,
            'contrast_ratio': round(ratio, 2),
            'threshold': threshold,
            'level': level,
            'text_size': text_size,
            'background_color': background_color,
            'text_color': text_color,
            'message': (f"✅ Contraste válido para WCAG {level} ({text_size}): {ratio}:1 >= {threshold}:1"
                        if is_valid else
                        f"❌ Contraste insuficiente para WCAG {level} ({text_size}): {ratio}:1 < {threshold}:1")
        }
