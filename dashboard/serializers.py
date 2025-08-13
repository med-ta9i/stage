from rest_framework import serializers
from .models import Equipment, EquipmentDesignation, EquipmentFamily, EquipmentLocation, EquipmentSubfamily

class EquipmentDesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentDesignation
        fields = ['equipment_designation_id', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class EquipmentFamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentFamily
        fields = ['family_id', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class EquipmentLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentLocation
        fields = ['site_id', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class EquipmentSubfamilySerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentSubfamily
        fields = ['subfamily_id', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class EquipmentSerializer(serializers.ModelSerializer):
    # Relations imbriquées
    designations = EquipmentDesignationSerializer(many=True, read_only=True)
    families = EquipmentFamilySerializer(many=True, read_only=True)
    locations = EquipmentLocationSerializer(many=True, read_only=True)
    subfamilies = EquipmentSubfamilySerializer(many=True, read_only=True)
    
    class Meta:
        model = Equipment
        fields = [
            '_id', 'model', 'serial', 'barcode', 'price', 'currency', 
            'status', 'description', 'config_user', 'creation_date', 
            'dms', 'photo', 'power', 'files', 'location',
            'created_at', 'updated_at',
            'designations', 'families', 'locations', 'subfamilies'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            '_id': {'read_only': True}
        }
    
    def to_representation(self, instance):
        """
        Surcharge pour formater correctement les dates et les champs spéciaux
        """
        representation = super().to_representation(instance)
        
        # Formater les dates
        date_fields = ['creation_date', 'dms', 'created_at', 'updated_at']
        for field in date_fields:
            if field in representation and representation[field]:
                representation[field] = representation[field].isoformat()
        
        # Formater le prix avec la devise
        if 'price' in representation and representation['price'] is not None:
            currency = representation.get('currency', 'MAD')
            representation['price_display'] = f"{representation['price']} {currency}"
        
        return representation
