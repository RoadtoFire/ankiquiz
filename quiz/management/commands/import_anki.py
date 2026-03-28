import json
import os
import re
import shutil
import sqlite3

from django.conf import settings
from django.core.management.base import BaseCommand

from quiz.models import Card, Deck, Note


class Command(BaseCommand):
    help = 'Import Anki deck from collection.anki2 into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--anki-db',
            type=str,
            required=True,
            help='Path to collection.anki2 file'
        )
        parser.add_argument(
            '--media-dir',
            type=str,
            required=True,
            help='Path to Anki collection.media folder'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip notes already in the database (faster resume)'
        )

    def handle(self, *args, **options):
        anki_db_path = options['anki_db']
        media_dir = options['media_dir']
        skip_existing = options.get('skip_existing')

        self.stdout.write('Connecting to Anki database...')
        conn = sqlite3.connect(anki_db_path)
        cursor = conn.cursor()

        # --- Step 1: Import Decks ---
        self.stdout.write('Importing decks...')

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        deck_map = {}

        if 'decks' in tables:
            cursor.execute("SELECT id, name FROM decks")
            for deck_id, deck_name in cursor.fetchall():
                deck, created = Deck.objects.get_or_create(
                    anki_id=str(deck_id),
                    defaults={'name': deck_name}
                )
                deck_map[str(deck_id)] = deck
                if created:
                    self.stdout.write(f'  Created deck: {deck_name}')
        else:
            cursor.execute("SELECT decks FROM col")
            row = cursor.fetchone()
            decks_json = json.loads(row[0])
            for deck_id, deck_data in decks_json.items():
                deck_name = deck_data.get('name', 'Unknown')
                deck, created = Deck.objects.get_or_create(
                    anki_id=str(deck_id),
                    defaults={'name': deck_name}
                )
                deck_map[str(deck_id)] = deck
                if created:
                    self.stdout.write(f'  Created deck: {deck_name}')

        # --- Step 2: Import Notes ---
        self.stdout.write('Importing notes...')

        cursor.execute("SELECT nid, did FROM cards")
        note_deck_map = {}
        for nid, did in cursor.fetchall():
            note_deck_map[nid] = str(did)

        cursor.execute("SELECT id, flds, tags FROM notes")
        notes = cursor.fetchall()

        fallback_deck = list(deck_map.values())[0] if deck_map else None

        existing_ids = set()
        if skip_existing:
            self.stdout.write('  Fetching existing note ids...')
            existing_ids = set(
                Note.objects.values_list('anki_note_id', flat=True)
            )
            self.stdout.write(f'  Skipping {len(existing_ids)} already imported notes')

        note_map = {}
        new_count = 0
        for note_id, flds, tags in notes:
            if skip_existing and note_id in existing_ids:
                note_map[note_id] = None
                continue
            has_images = '<img' in flds
            deck_id = note_deck_map.get(note_id)
            deck = deck_map.get(deck_id, fallback_deck)
            note, created = Note.objects.get_or_create(
                anki_note_id=note_id,
                defaults={
                    'deck': deck,
                    'fields_raw': flds,
                    'tags': tags.strip(),
                    'has_images': has_images,
                }
            )
            note_map[note_id] = note
            if created:
                new_count += 1

        self.stdout.write(f'  Imported {new_count} new notes')

        # --- Step 3: Import Cards ---
        self.stdout.write('Importing cards...')
        cursor.execute("SELECT id, nid, ord FROM cards")
        cards = cursor.fetchall()

        # When skipping existing notes, note_map has None values
        # Build a lookup from the database directly
        if skip_existing:
            self.stdout.write('  Building note lookup from database...')
            from quiz.models import Note as NoteModel
            note_map = {
                n.anki_note_id: n
                for n in NoteModel.objects.all()
            }

        card_count = 0
        for card_id, note_id, ord_ in cards:
            if note_id not in note_map or note_map[note_id] is None:
                continue
            Card.objects.get_or_create(
                anki_card_id=card_id,
                defaults={
                    'note': note_map[note_id],
                    'ordinal': ord_,
                }
            )
            card_count += 1

        self.stdout.write(f'  Imported {card_count} new cards')

        conn.close()

        # --- Step 4: Copy Media Files ---
        self.stdout.write('Copying media files...')
        media_root = settings.MEDIA_ROOT
        os.makedirs(media_root, exist_ok=True)

        copied = 0
        for filename in os.listdir(media_dir):
            src = os.path.join(media_dir, filename)
            dst = os.path.join(media_root, filename)
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                copied += 1

        self.stdout.write(f'  Copied {copied} media files')
        self.stdout.write(self.style.SUCCESS('Import complete!'))