from rest_framework import serializers
from .analytics import convert_units
from .models import (
    Ingredient,
    CocktailRecipe,
    RecipeIngredient,
    CocktailConsumption,
    CocktailIngredientConsumption
)

# --- Ingredient Serializer ---
class IngredientSerializer(serializers.ModelSerializer):
    hotel_id = serializers.IntegerField(write_only=True)
    linked_stock_item_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
        help_text="Optional: Link to a stock item for tracking"
    )
    linked_stock_item = serializers.SerializerMethodField()
    
    class Meta:
        model = Ingredient
        fields = [
            'id',
            'name',
            'unit',
            'hotel_id',
            'linked_stock_item_id',
            'linked_stock_item'
        ]
    
    def get_linked_stock_item(self, obj):
        """Return basic info about linked stock item if available"""
        if obj.linked_stock_item:
            return {
                'id': obj.linked_stock_item.id,
                'sku': obj.linked_stock_item.sku,
                'name': obj.linked_stock_item.name
            }
        return None


# --- RecipeIngredient Serializer ---
class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source='ingredient', write_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'ingredient', 'ingredient_id', 'quantity_per_cocktail']


# --- CocktailRecipe Serializer ---
class CocktailRecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    hotel_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CocktailRecipe
        fields = ['id', 'name', 'ingredients', 'hotel_id', 'price']

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        cocktail = CocktailRecipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(cocktail=cocktail, **ingredient_data)
        return cocktail

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        instance.name = validated_data.get('name', instance.name)
        instance.price = validated_data.get('price', instance.price)
        instance.save()

        if ingredients_data is not None:
            # Replace all existing ingredients
            instance.ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(cocktail=instance, **ingredient_data)
        return instance


# --- CocktailConsumption Serializer ---

class CocktailConsumptionSerializer(serializers.ModelSerializer):
    cocktail = serializers.StringRelatedField(read_only=True)
    cocktail_id = serializers.PrimaryKeyRelatedField(
        queryset=CocktailRecipe.objects.all(),
        source='cocktail',
        write_only=True
    )
    total_ingredient_usage = serializers.SerializerMethodField()
    profit = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )
    # Nested ingredient consumptions (created automatically on save)
    ingredient_consumptions = serializers.SerializerMethodField()

    class Meta:
        model = CocktailConsumption
        fields = [
            'id',
            'cocktail',
            'cocktail_id',
            'quantity_made',
            'timestamp',
            'unit_price',
            'total_revenue',
            'total_cost',
            'profit',
            'total_ingredient_usage',
            'ingredient_consumptions',
        ]
        read_only_fields = [
            'total_revenue',
            'total_cost',
            'timestamp',
            'ingredient_consumptions'
        ]

    def get_total_ingredient_usage(self, obj):
        raw_usage = obj.total_ingredient_usage()  # {(qty, unit)}
        return convert_units(raw_usage)
    
    def get_ingredient_consumptions(self, obj):
        """
        Return simplified ingredient consumption data.
        For full details, use CocktailIngredientConsumptionSerializer.
        """
        consumptions = obj.ingredient_consumptions.all()
        return [{
            'id': c.id,
            'ingredient_name': c.ingredient.name,
            'quantity_used': str(c.quantity_used),
            'unit': c.unit,
            'stock_item_sku': c.stock_item.sku if c.stock_item else None,
            'is_merged': c.is_merged_to_stocktake,
            'can_be_merged': c.can_be_merged
        } for c in consumptions]

    def create(self, validated_data):
        # Get hotel from request user if available
        request = self.context.get('request')
        if request and hasattr(request.user, 'hotel_id'):
            validated_data['hotel_id'] = request.user.hotel_id
        else:
            # fallback: use the cocktail's hotel
            cocktail = validated_data['cocktail']
            validated_data['hotel'] = cocktail.hotel

        return super().create(validated_data)


# --- CocktailIngredientConsumption Serializer ---

class CocktailIngredientConsumptionSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing individual ingredient consumption records.
    Shows what ingredients were used in cocktails and their merge status.
    """
    # Cocktail info
    cocktail_name = serializers.CharField(
        source='cocktail_consumption.cocktail.name',
        read_only=True
    )
    cocktail_consumption_id = serializers.IntegerField(
        source='cocktail_consumption.id',
        read_only=True
    )
    quantity_made = serializers.IntegerField(
        source='cocktail_consumption.quantity_made',
        read_only=True
    )
    
    # Ingredient info
    ingredient_name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    
    # Stock item info (if linked)
    stock_item_sku = serializers.CharField(
        source='stock_item.sku',
        read_only=True,
        allow_null=True
    )
    stock_item_name = serializers.CharField(
        source='stock_item.name',
        read_only=True,
        allow_null=True
    )
    
    # Merge tracking
    merged_by_name = serializers.SerializerMethodField()
    stocktake_id = serializers.IntegerField(
        source='merged_to_stocktake.id',
        read_only=True,
        allow_null=True
    )
    
    # Calculated fields
    can_be_merged = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CocktailIngredientConsumption
        fields = [
            'id',
            # Cocktail info
            'cocktail_consumption_id',
            'cocktail_name',
            'quantity_made',
            # Ingredient info
            'ingredient',
            'ingredient_name',
            'quantity_used',
            'unit',
            # Stock item link
            'stock_item',
            'stock_item_sku',
            'stock_item_name',
            # Cost tracking
            'unit_cost',
            'total_cost',
            # Merge tracking
            'is_merged_to_stocktake',
            'merged_at',
            'merged_by',
            'merged_by_name',
            'stocktake_id',
            'can_be_merged',
            # Metadata
            'timestamp'
        ]
        read_only_fields = [
            'is_merged_to_stocktake',
            'merged_at',
            'merged_by',
            'timestamp',
            'can_be_merged'
        ]
    
    def get_merged_by_name(self, obj):
        """Return name of staff who merged this consumption"""
        if obj.merged_by:
            return (
                f"{obj.merged_by.user.first_name} "
                f"{obj.merged_by.user.last_name}"
            ).strip() or obj.merged_by.user.username
        return None
