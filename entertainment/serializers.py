from rest_framework import serializers
from .models import Game, GameHighScore, GameQRCode

class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ['id', 'title', 'slug', 'description', 'thumbnail', 'active']


class GameHighScoreSerializer(serializers.ModelSerializer):
    player = serializers.SerializerMethodField()
    game = serializers.StringRelatedField(read_only=True)
    hotel = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GameHighScore
        fields = ['id', 'player', 'game', 'hotel', 'score', 'achieved_at']

    def get_player(self, obj):
        return obj.player_name or (obj.user.username if obj.user else "Anonymous")


class GameHighScoreCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameHighScore
        fields = ['game', 'hotel', 'score', 'player_name']

    # create() no longer needs to handle get-or-create, handled in view
    def create(self, validated_data):
        user = self.context['request'].user if self.context['request'].user.is_authenticated else None
        return GameHighScore.objects.create(user=user, **validated_data)


class GameQRCodeSerializer(serializers.ModelSerializer):
    game = serializers.StringRelatedField(read_only=True)
    hotel = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GameQRCode
        fields = ['id', 'game', 'hotel', 'qr_url', 'generated_at']
