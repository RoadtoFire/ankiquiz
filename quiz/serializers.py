import re

from django.conf import settings
from rest_framework import serializers

from .models import Card, Deck, Note


class DeckSerializer(serializers.ModelSerializer):
    note_count = serializers.IntegerField(source='notes.count', read_only=True)

    class Meta:
        model = Deck
        fields = ['id', 'name', 'anki_id', 'note_count']


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'anki_card_id', 'ordinal']


class NoteSerializer(serializers.ModelSerializer):
    deck = DeckSerializer(read_only=True)
    cards = CardSerializer(many=True, read_only=True)
    content = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ['id', 'anki_note_id', 'deck', 'content', 'tags_list', 'has_images', 'cards']

    def get_content(self, obj):
        fields = obj.get_fields()
        text = fields[0] if len(fields) > 0 else ''
        extra = fields[1] if len(fields) > 1 else ''

        request = self.context.get('request')
        if request:
            text = self._rewrite_img_urls(text, request)
            extra = self._rewrite_img_urls(extra, request)

        return {
            'text': text,
            'extra': extra,
        }

    def _rewrite_img_urls(self, html, request):
        def replace(match):
            filename = match.group(1)
            url = request.build_absolute_uri(f'{settings.MEDIA_URL}{filename}')
            return f'src="{url}"'
        return re.sub(r'src="([^"]+)"', replace, html)

    def get_tags_list(self, obj):
        if not obj.tags:
            return []
        return obj.tags.strip().split()


class NoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views - no cards, no deck detail"""
    tags_list = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ['id', 'anki_note_id', 'text', 'tags_list', 'has_images']

    def get_text(self, obj):
        text = obj.get_fields()[0]
        request = self.context.get('request')
        if request:
            text = self._rewrite_img_urls(text, request)
        return text

    def _rewrite_img_urls(self, html, request):
        def replace(match):
            filename = match.group(1)
            url = request.build_absolute_uri(f'{settings.MEDIA_URL}{filename}')
            return f'src="{url}"'
        return re.sub(r'src="([^"]+)"', replace, html)

    def get_tags_list(self, obj):
        if not obj.tags:
            return []
        return obj.tags.strip().split()