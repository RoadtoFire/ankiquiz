import os
import cloudinary.uploader
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Upload Anki media files to Cloudinary'

    def add_arguments(self, parser):
        parser.add_argument(
            '--media-dir',
            type=str,
            required=True,
            help='Path to Anki collection.media folder'
        )

    def handle(self, *args, **options):
        media_dir = options['media_dir']
        files = os.listdir(media_dir)
        total = len(files)

        self.stdout.write(f'Uploading {total} files to Cloudinary...')

        uploaded = 0
        skipped = 0
        for i, filename in enumerate(files, 1):
            filepath = os.path.join(media_dir, filename)
            name, ext = os.path.splitext(filename)

            try:
                cloudinary.uploader.upload(
                    filepath,
                    public_id=name,
                    overwrite=False,
                    resource_type='auto',
                )
                uploaded += 1
            except Exception as e:
                if 'already exists' in str(e).lower():
                    skipped += 1
                else:
                    self.stdout.write(f'  Error uploading {filename}: {e}')

            if i % 50 == 0:
                self.stdout.write(f'  Progress: {i}/{total}')

        self.stdout.write(self.style.SUCCESS(f'Done! Uploaded: {uploaded}, Skipped: {skipped}'))