from django.db import models


class Deck(models.Model):
    name = models.CharField(max_length=255)
    anki_id = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Note(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='notes')
    anki_note_id = models.BigIntegerField(unique=True)
    fields_raw = models.TextField()
    tags = models.TextField(blank=True)
    has_images = models.BooleanField(default=False)
    # Store pre-processed HTML with Cloudinary URLs already injected
    fields_processed = models.TextField(blank=True)

    def get_fields(self):
        return self.fields_raw.split('\x1f')

    def get_processed_fields(self):
        if self.fields_processed:
            return self.fields_processed.split('\x1f')
        return self.get_fields()

    def __str__(self):
        return f"Note {self.anki_note_id} ({self.deck.name})"


class Card(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='cards')
    anki_card_id = models.BigIntegerField(unique=True)
    ordinal = models.IntegerField()        # which cloze number (0, 1, 2...)

    def __str__(self):
        return f"Card {self.anki_card_id} (Note {self.note.anki_note_id})"