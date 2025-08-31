# cocktail_serializers.py
from rest_framework import serializers
from .models import Ingredient, CocktailRecipe, RecipeIngredient, CocktailConsumption

# --- Ingredient Serializer ---
class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'unit']


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

    class Meta:
        model = CocktailRecipe
        fields = ['id', 'name', 'ingredients']

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        cocktail = CocktailRecipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(cocktail=cocktail, **ingredient_data)
        return cocktail

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        instance.name = validated_data.get('name', instance.name)
        instance.save()

        if ingredients_data is not None:
            # Replace all existing ingredients
            instance.ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(cocktail=instance, **ingredient_data)
        return instance


# --- CocktailConsumption Serializer ---
class CocktailConsumptionSerializer(serializers.ModelSerializer):
    cocktail = CocktailRecipeSerializer(read_only=True)
    cocktail_id = serializers.PrimaryKeyRelatedField(
        queryset=CocktailRecipe.objects.all(), source='cocktail', write_only=True
    )
    total_ingredient_usage = serializers.SerializerMethodField()

    class Meta:
        model = CocktailConsumption
        fields = ['id', 'cocktail', 'cocktail_id', 'quantity_made', 'timestamp', 'total_ingredient_usage']

    def get_total_ingredient_usage(self, obj):
        return obj.total_ingredient_usage()
