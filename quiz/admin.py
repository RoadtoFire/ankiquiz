from django.contrib import admin

from .models import Card, Deck, Note


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ['name', 'note_count']
    search_fields = ['name']

    def note_count(self, obj):
        return obj.notes.count()
    note_count.short_description = 'Notes'


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['anki_note_id', 'deck', 'has_images', 'tags']
    list_filter = ['deck', 'has_images']
    search_fields = ['tags', 'fields_raw']
    raw_id_fields = ['deck']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['anki_card_id', 'note', 'ordinal']
    raw_id_fields = ['note']