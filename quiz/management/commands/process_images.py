import os
import re
import cloudinary
import cloudinary.api
from django.core.management.base import BaseCommand
from quiz.models import Note


def rewrite_img_urls(html):
    def replace(match):
        filename = match.group(1).strip().rstrip('\\').rstrip('/')
        name, ext = os.path.splitext(filename)
        ext = ext.lstrip('.')
        try:
            result = cloudinary.api.resource(name)
            url = result['secure_url']
            return f'src="{url}"'
        except Exception:
            return match.group(0)
    return re.sub(r'src="([^"]+)"', replace, html)


class Command(BaseCommand):
    help = 'Pre-process notes to inject Cloudinary URLs'

    def handle(self, *args, **options):
        notes = Note.objects.filter(has_images=True, fields_processed='')
        total = notes.count()
        self.stdout.write(f'Processing {total} notes with images...')

        for i, note in enumerate(notes, 1):
            fields = note.get_fields()
            processed = []
            for field in fields:
                if '<img' in field:
                    processed.append(rewrite_img_urls(field))
                else:
                    processed.append(field)
            note.fields_processed = '\x1f'.join(processed)
            note.save()

            if i % 100 == 0:
                self.stdout.write(f'  Progress: {i}/{total}')

        self.stdout.write(self.style.SUCCESS('Done!'))