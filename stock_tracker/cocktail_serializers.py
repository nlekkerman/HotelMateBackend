from rest_framework import serializers
from .analytics import convert_units
from .models import Ingredient, CocktailRecipe, RecipeIngredient, CocktailConsumption

# --- Ingredient Serializer ---
class IngredientSerializer(serializers.ModelSerializer):
    hotel_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'unit', 'hotel_id']


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
        queryset=CocktailRecipe.objects.all(), source='cocktail', write_only=True
    )
    total_ingredient_usage = serializers.SerializerMethodField()
    profit = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )

    class Meta:
        model = CocktailConsumption
        fields = [
            'id',
            'cocktail',
            'cocktail_id',
            'quantity_made',
            'timestamp',
            'stocktake',
            'unit_price',
            'total_revenue',
            'total_cost',
            'profit',
            'total_ingredient_usage',
        ]
        read_only_fields = ['total_revenue', 'total_cost', 'timestamp']

    def get_total_ingredient_usage(self, obj):
        raw_usage = obj.total_ingredient_usage()  # {(qty, unit)}
        return convert_units(raw_usage)

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
