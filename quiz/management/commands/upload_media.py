import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
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

        self.stdout.write(f'Fetching existing Cloudinary assets...')
        existing = set()
        next_cursor = None
        while True:
            result = cloudinary.api.resources(
                max_results=500,
                next_cursor=next_cursor,
                resource_type='image'
            )
            for r in result['resources']:
                existing.add(r['public_id'])
            next_cursor = result.get('next_cursor')
            if not next_cursor:
                break
        self.stdout.write(f'  Found {len(existing)} existing assets on Cloudinary')

        self.stdout.write(f'Uploading {total} files to Cloudinary...')
        uploaded = 0
        skipped = 0
        errors = 0

        for i, filename in enumerate(files, 1):
            filepath = os.path.join(media_dir, filename)
            name, ext = os.path.splitext(filename)

            if name in existing:
                skipped += 1
                if i % 50 == 0:
                    self.stdout.write(f'  Progress: {i}/{total}')
                continue

            try:
                cloudinary.uploader.upload(
                    filepath,
                    public_id=name,
                    overwrite=False,
                    resource_type='auto',
                )
                uploaded += 1
            except Exception as e:
                errors += 1
                if 'already exists' not in str(e).lower():
                    self.stdout.write(f'  Error uploading {filename}: {e}')

            if i % 50 == 0:
                self.stdout.write(f'  Progress: {i}/{total}')

        self.stdout.write(self.style.SUCCESS(
            f'Done! Uploaded: {uploaded}, Skipped: {skipped}, Errors: {errors}'
        ))