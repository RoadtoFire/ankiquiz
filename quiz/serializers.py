import os
import re

import cloudinary
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


def rewrite_img_urls(html):
    import cloudinary.api
    import logging
    logger = logging.getLogger(__name__)

    def replace(match):
        filename = match.group(1).strip().rstrip('\\').rstrip('/')
        name, ext = os.path.splitext(filename)
        try:
            result = cloudinary.api.resource(name)
            url = result['secure_url']
            logger.info(f'Cloudinary URL: {url}')
            return f'src="{url}"'
        except Exception as e:
            logger.error(f'Cloudinary error for {name}: {e}')
            return match.group(0)

    return re.sub(r'src="([^"]+)"', replace, html)


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
        return {
            'text': rewrite_img_urls(text),
            'extra': rewrite_img_urls(extra),
        }

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
        return rewrite_img_urls(obj.get_fields()[0])

    def get_tags_list(self, obj):
        if not obj.tags:
            return []
        return obj.tags.strip().split()