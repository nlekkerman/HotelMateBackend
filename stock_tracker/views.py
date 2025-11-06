from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .analytics import ingredient_usage
from .models import (
    Ingredient,
    CocktailRecipe,
    CocktailConsumption
)
from .cocktail_serializers import (
    IngredientSerializer,
    CocktailRecipeSerializer,
    CocktailConsumptionSerializer
)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    search_fields = ['name']
    ordering_fields = ['name']


class CocktailRecipeViewSet(viewsets.ModelViewSet):
    queryset = CocktailRecipe.objects.prefetch_related(
        'ingredients__ingredient'
    ).all()
    serializer_class = CocktailRecipeSerializer
    search_fields = ['name']
    ordering_fields = ['name']


class CocktailConsumptionViewSet(viewsets.ModelViewSet):
    queryset = CocktailConsumption.objects.select_related('cocktail').all()
    serializer_class = CocktailConsumptionSerializer
    ordering = ['-timestamp']

    def get_queryset(self):
        qs = super().get_queryset()
        cocktail_id = self.request.query_params.get('cocktail_id')
        if cocktail_id:
            qs = qs.filter(cocktail_id=cocktail_id)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class IngredientUsageView(APIView):
    def get(self, request):
        hotel_id = request.query_params.get('hotel_id')

        try:
            data = ingredient_usage(hotel_id=hotel_id)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(data, status=status.HTTP_200_OK)
