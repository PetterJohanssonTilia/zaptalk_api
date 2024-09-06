import json
from django.core.management.base import BaseCommand
from api.models import Movie

class Command(BaseCommand):
    help = 'Import movies from JSON file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file')

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']
        with open(json_file, 'r') as file:
            movies_data = json.load(file)

        success_count = 0
        error_count = 0

        for index, movie_data in enumerate(movies_data):
            try:
                Movie.objects.create(
                    title=movie_data.get('title', ''),
                    year=movie_data.get('year', 0),
                    cast=movie_data.get('cast', []),
                    genres=movie_data.get('genres', []),
                    href=movie_data.get('href', None),
                    extract=movie_data.get('extract', ''),
                    thumbnail=movie_data.get('thumbnail', ''),
                    thumbnail_width=movie_data.get('thumbnail_width'),
                    thumbnail_height=movie_data.get('thumbnail_height')
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'Error importing movie at index {index}: {str(e)}'))
                self.stdout.write(self.style.ERROR(f'Problematic data: {movie_data}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully imported {success_count} movies'))
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'Encountered errors while importing {error_count} movies'))