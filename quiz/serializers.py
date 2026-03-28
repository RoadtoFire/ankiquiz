import os
import re

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
        fields = obj.get_processed_fields()
        text = fields[0] if len(fields) > 0 else ''
        extra = fields[1] if len(fields) > 1 else ''
        return {
            'text': text,
            'extra': extra,
        }

    def get_tags_list(self, obj):
        if not obj.tags:
            return []
        return obj.tags.strip().split()


class NoteListSerializer(serializers.ModelSerializer):
    tags_list = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ['id', 'anki_note_id', 'text', 'tags_list', 'has_images']

    def get_text(self, obj):
        return obj.get_processed_fields()[0]

    def get_tags_list(self, obj):
        if not obj.tags:
            return []
        return obj.tags.strip().split()