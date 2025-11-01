from rest_framework import serializers
from service_requests.models.invoice_line import InvoiceLine
from django.core.validators import MinValueValidator, MaxValueValidator
from django.apps import apps
from decimal import Decimal

TRIBUTE_ID = 1
STANDARD_CODE_ID = 1  

class InvoiceLineSerializer(serializers.ModelSerializer):
    service_item = serializers.PrimaryKeyRelatedField(
        queryset=apps.get_model('service_requests', 'Service').objects.all()
    )
    service_item_name = serializers.CharField(source='service_item.service_name', read_only=True)

    quantity = serializers.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Cantidad del servicio (mayor a 0)."
    )
    discount_percentage = serializers.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de descuento (0-100)."
    )
    discount_amount = serializers.SerializerMethodField(read_only=True)
    
    units_measurement_id = serializers.IntegerField(
        default=70,
        help_text="ID de unidad de medida (default: 70)."
    )
    total_line_amount = serializers.SerializerMethodField(read_only=True)
    
    percentage_taxes_per_line = serializers.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de impuesto (0-100)."
    )
    
    # Retenciones por línea (opcional)
    withholding_taxes = serializers.ListField(
        child=serializers.DictField(), required=False, allow_null=True,
        help_text="Lista de retenciones por línea. Ej: [{code:'06', withholding_tax_rate:7.38}]"
    )

    # tribute_id: opcional en input. Por defecto 1
    tribute_id = serializers.IntegerField(
        default=1,
        help_text="ID del tributo (por defecto: 1). Debe corresponder al catálogo disponible en frontend."
    )

    withholding_total_amount = serializers.SerializerMethodField(read_only=True)

    # Campo calculado para Factus (read-only)
    factus_payload = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InvoiceLine
        fields = (
            'id_invoice_line',
            'service_item',
            'service_item_name',
            'quantity',
            'discount_percentage',
            'discount_amount',
            'price_unit',
            'tax_per_line_type',
            'percentage_taxes_per_line',
            'units_measurement_id',
            'withholding_taxes',
            'withholding_total_amount',
            'total_line_amount',
            'service_name',
            'code_reference',
        'tribute_id',
            'invoice',
            'factus_payload',
        )
        read_only_fields = [
            'price_unit',
            'tax_per_line_type',
            'service_name',
            'code_reference',
            'invoice',
            'factus_payload',
            'discount_amount',
            'total_line_amount',
            'withholding_total_amount',
        ]

    def validate(self, data):
        # Validar cantidad
        if data.get('quantity', 0) <= 0:
            raise serializers.ValidationError({"quantity": "La cantidad debe ser mayor a cero."})
        
        # Validar descuento
        if data.get('discount_percentage', 0) < 0 or data.get('discount_percentage', 0) > 100:
            raise serializers.ValidationError({"discount_percentage": "El descuento debe estar entre 0 y 100%."})
        
        # Validar impuesto
        if data.get('percentage_taxes_per_line', 0) < 0 or data.get('percentage_taxes_per_line', 0) > 100:
            raise serializers.ValidationError({"percentage_taxes_per_line": "El impuesto debe estar entre 0 y 100%."})
        
        # Validar que service_item esté activo (usa service_status_id de Service)
        service_item = data.get('service_item')
        if service_item is not None:
            status_id = getattr(service_item, 'service_status_id', None)
            if status_id is not None and status_id != 1:  # 1 = Activo
                raise serializers.ValidationError({"service_item": "El servicio seleccionado no está activo."})

        # Validar unidad de medida contra Factus
        unit = data.get('units_measurement_id')
        if unit is not None:
            # Asegurar entero válido primero
            try:
                unit_int = int(unit)
            except (TypeError, ValueError):
                raise serializers.ValidationError({
                    "units_measurement_id": "La unidad de medida debe ser un número entero."
                })

            # Consultar catálogo en Factus
            exists = False
            try:
                from core.services.factus_service import FactusService
                exists = FactusService().validate_measurement_unit(unit_int)
            except Exception:
                exists = False

            if not exists:
                raise serializers.ValidationError({
                    "units_measurement_id": "La unidad de medida no existe en Factus."
                })

        # Validar estructura de retenciones si vienen
        wt = data.get('withholding_taxes', None)
        if wt is not None:
            if not isinstance(wt, (list, tuple)):
                raise serializers.ValidationError({
                    "withholding_taxes": "Debe ser una lista de objetos {code, withholding_tax_rate}."
                })
            cleaned_list = []
            for idx, item in enumerate(wt):
                if not isinstance(item, dict):
                    raise serializers.ValidationError({
                        "withholding_taxes": f"Elemento #{idx+1} debe ser un objeto."
                    })
                code = item.get('code')
                rate = item.get('withholding_tax_rate')
                if not code or not isinstance(code, str):
                    raise serializers.ValidationError({
                        "withholding_taxes": f"Elemento #{idx+1}: 'code' es requerido y debe ser string."
                    })
                try:
                    rate_val = float(rate)
                except (TypeError, ValueError):
                    raise serializers.ValidationError({
                        "withholding_taxes": f"Elemento #{idx+1}: 'withholding_tax_rate' debe ser numérico."
                    })
                if rate_val < 0 or rate_val > 100:
                    raise serializers.ValidationError({
                        "withholding_taxes": f"Elemento #{idx+1}: 'withholding_tax_rate' debe estar entre 0 y 100."
                    })
                cleaned_list.append({"code": code, "withholding_tax_rate": rate_val})
            # Sustituimos por la versión normalizada (floats)
            data['withholding_taxes'] = cleaned_list
        
        # Validar tribute_id si viene
        tribute_val = data.get('tribute_id', None)
        if tribute_val is not None:
            try:
                tribute_int = int(tribute_val)
            except (TypeError, ValueError):
                raise serializers.ValidationError({
                    "tribute_id": "El campo tribute_id debe ser un número entero válido."
                })

            # Lista de tributos válidos que usa el frontend (IDs conocidos)
            VALID_TRIBUTE_IDS = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17}
            if tribute_int not in VALID_TRIBUTE_IDS:
                raise serializers.ValidationError({
                    "tribute_id": "El tributo especificado no es válido."
                })

            data['tribute_id'] = tribute_int

        return data

    def create(self, validated_data):
        service_item = validated_data.get('service_item')
        
        # Extraer campos del Service para Factus
        validated_data['price_unit'] = service_item.base_price
        validated_data['percentage_taxes_per_line'] = validated_data.get('percentage_taxes_per_line', service_item.tax_rate)
        validated_data['service_name'] = service_item.service_name
        validated_data['code_reference'] = service_item.id_service
        
        if 'units_measurement_id' not in validated_data:
            validated_data['units_measurement_id'] = 70

        if 'tribute_id' not in validated_data:
            validated_data['tribute_id'] = 1
        
        # Obtener dinámicamente el tax_per_line_type desde Factus según el tribute_id
        tribute_id = validated_data.get('tribute_id', 1)
        try:
            from core.services.factus_service import FactusService
            tax_type = FactusService().get_tribute_tax_type(tribute_id)
            validated_data['tax_per_line_type'] = tax_type
        except Exception as e:
            # En caso de error, usar 'IVA' por defecto
            validated_data['tax_per_line_type'] = 'IVA'
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'service_item' in validated_data:
            validated_data.pop('service_item')
        
        validated_data['price_unit'] = instance.price_unit
        validated_data['code_reference'] = instance.code_reference
        if 'tribute_id' not in validated_data:
            validated_data['tribute_id'] = instance.tribute_id
        
        # Si se actualiza el tribute_id, actualizar también el tax_per_line_type
        tribute_id = validated_data.get('tribute_id', instance.tribute_id)
        try:
            from core.services.factus_service import FactusService
            tax_type = FactusService().get_tribute_tax_type(tribute_id)
            validated_data['tax_per_line_type'] = tax_type
        except Exception as e:
            # En caso de error, mantener el valor actual o usar 'IVA' por defecto
            if not instance.tax_per_line_type:
                validated_data['tax_per_line_type'] = 'IVA'
        
        return super().update(instance, validated_data)

    def get_factus_payload(self, obj):
        """
        Genera el payload para Factus según la documentación.
        """
        # Normalizar retenciones (puede ser None)
        wt_list = obj.withholding_taxes or []
        normalized_wt = []
        for item in wt_list:
            code = str(item.get('code')) if isinstance(item, dict) else None
            rate = item.get('withholding_tax_rate') if isinstance(item, dict) else None
            if code and rate is not None:
                try:
                    rate_val = float(rate)
                except (TypeError, ValueError):
                    continue
                normalized_wt.append({
                    "code": code,
                    "withholding_tax_rate": rate_val,
                })

        return {
            "code_reference": str(obj.code_reference),
            "name": obj.service_name,
            "quantity": float(obj.quantity),
            "discount_rate": float(obj.discount_percentage),
            "price": float(obj.price_unit),
            "tax_rate": str(obj.percentage_taxes_per_line),
            "unit_measure_id": obj.units_measurement_id,
            "standard_code_id": STANDARD_CODE_ID,
            "is_excluded": 0 if not obj.service_item.is_vat_exempt else 1,
            # Enviar el tribute_id que venga en la línea (por defecto 1)
            "tribute_id": int(obj.tribute_id) if obj.tribute_id is not None else 1,
            "withholding_taxes": normalized_wt,
        }

    def get_discount_amount(self, obj):
        """
        Calcula el monto del descuento: (price_unit * quantity) * (discount_percentage / 100)
        """
        subtotal = Decimal(obj.price_unit) * Decimal(obj.quantity)
        discount_amount = subtotal * (Decimal(obj.discount_percentage) / Decimal(100))
        return float(discount_amount)

    def get_total_line_amount(self, obj):
        """
        Calcula el total de la línea incluyendo descuentos e impuestos:
        1. Subtotal = price_unit * quantity
        2. Descuento = subtotal * (discount_percentage / 100)
        3. Subtotal después de descuento = subtotal - descuento
        4. Impuesto = subtotal_despues_descuento * (percentage_taxes_per_line / 100)
        5. Retenciones (si existen) = subtotal_despues_descuento * (withholding_tax_rate / 100) por cada una
        6. Total = subtotal_despues_descuento + impuesto - retenciones
        """
        subtotal = Decimal(obj.price_unit) * Decimal(obj.quantity)
        discount_amount = subtotal * (Decimal(obj.discount_percentage) / Decimal(100))
        subtotal_after_discount = subtotal - discount_amount
        tax_amount = subtotal_after_discount * (Decimal(obj.percentage_taxes_per_line) / Decimal(100))
        # Calcular retenciones (aplicadas sobre base imponible por defecto)
        withholding_total = Decimal('0.00')
        if obj.withholding_taxes:
            for item in obj.withholding_taxes:
                try:
                    rate = Decimal(str(item.get('withholding_tax_rate', 0)))
                except Exception:
                    rate = Decimal('0')
                if rate > 0:
                    withholding_total += subtotal_after_discount * (rate / Decimal(100))
        total = subtotal_after_discount + tax_amount - withholding_total
        return float(total)

    def get_withholding_total_amount(self, obj):
        """
        Suma de las retenciones aplicadas a la línea, usando la convención:
        base = subtotal después de descuento.
        """
        subtotal = Decimal(obj.price_unit) * Decimal(obj.quantity)
        discount_amount = subtotal * (Decimal(obj.discount_percentage) / Decimal(100))
        base = subtotal - discount_amount
        total_wt = Decimal('0.00')
        if obj.withholding_taxes:
            for item in obj.withholding_taxes:
                try:
                    rate = Decimal(str(item.get('withholding_tax_rate', 0)))
                except Exception:
                    rate = Decimal('0')
                if rate > 0:
                    total_wt += base * (rate / Decimal(100))
        return float(total_wt)
