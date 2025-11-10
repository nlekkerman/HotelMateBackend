"""
Serializers for enhanced period comparison endpoints.
Optimized for frontend charts and visualizations.
"""
from rest_framework import serializers


class CategoryComparisonSerializer(serializers.Serializer):
    """Serializer for category-level comparison between two periods"""
    code = serializers.CharField()
    name = serializers.CharField()
    
    period1 = serializers.DictField(child=serializers.DecimalField(
        max_digits=12, decimal_places=2
    ))
    period2 = serializers.DictField(child=serializers.DecimalField(
        max_digits=12, decimal_places=2
    ))
    change = serializers.DictField()


class CategoryComparisonResponseSerializer(serializers.Serializer):
    """Response serializer for compare_categories endpoint"""
    period1 = serializers.DictField()
    period2 = serializers.DictField()
    categories = CategoryComparisonSerializer(many=True)
    summary = serializers.DictField()


class TopMoverItemSerializer(serializers.Serializer):
    """Serializer for individual item in top movers analysis"""
    item_id = serializers.IntegerField()
    sku = serializers.CharField()
    name = serializers.CharField()
    category = serializers.CharField()
    period1_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    period2_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    absolute_change = serializers.DecimalField(
        max_digits=12, decimal_places=2
    )
    percentage_change = serializers.DecimalField(
        max_digits=10, decimal_places=2
    )
    reason = serializers.CharField()


class TopMoversResponseSerializer(serializers.Serializer):
    """Response serializer for top_movers endpoint"""
    biggest_increases = TopMoverItemSerializer(many=True)
    biggest_decreases = TopMoverItemSerializer(many=True)
    new_items = serializers.ListField(child=serializers.DictField())
    discontinued_items = serializers.ListField(child=serializers.DictField())


class CostAnalysisResponseSerializer(serializers.Serializer):
    """Response serializer for cost_analysis endpoint"""
    period1 = serializers.DictField()
    period2 = serializers.DictField()
    comparison = serializers.DictField()
    waterfall_data = serializers.ListField(child=serializers.DictField())


class TrendDataPointSerializer(serializers.Serializer):
    """Individual data point in trend analysis"""
    period_id = serializers.IntegerField()
    value = serializers.DecimalField(max_digits=12, decimal_places=2)
    servings = serializers.DecimalField(max_digits=10, decimal_places=2)
    waste = serializers.DecimalField(max_digits=12, decimal_places=2)


class TrendItemSerializer(serializers.Serializer):
    """Serializer for item trend data"""
    item_id = serializers.IntegerField()
    sku = serializers.CharField()
    name = serializers.CharField()
    category = serializers.CharField()
    trend_data = TrendDataPointSerializer(many=True)
    trend_direction = serializers.CharField()
    average_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    volatility = serializers.CharField()


class TrendAnalysisResponseSerializer(serializers.Serializer):
    """Response serializer for trend_analysis endpoint"""
    periods = serializers.ListField(child=serializers.DictField())
    items = TrendItemSerializer(many=True)


class VarianceHeatmapResponseSerializer(serializers.Serializer):
    """Response serializer for variance_heatmap endpoint"""
    periods = serializers.ListField(child=serializers.CharField())
    categories = serializers.ListField(child=serializers.CharField())
    heatmap_data = serializers.ListField(child=serializers.ListField())
    color_scale = serializers.DictField()


class PerformanceMetricSerializer(serializers.Serializer):
    """Individual performance metric"""
    name = serializers.CharField()
    period1_score = serializers.IntegerField()
    period2_score = serializers.IntegerField()
    weight = serializers.DecimalField(max_digits=3, decimal_places=2)
    status = serializers.CharField()


class PerformanceScorecardResponseSerializer(serializers.Serializer):
    """Response serializer for performance_scorecard endpoint"""
    overall_score = serializers.DictField()
    metrics = PerformanceMetricSerializer(many=True)
    radar_chart_data = serializers.DictField()
