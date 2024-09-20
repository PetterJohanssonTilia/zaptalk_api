from django.core.management.base import BaseCommand
from api.models import Movie

class Command(BaseCommand):
    help = 'Inspect movie genres in the database'

    def handle(self, *args, **options):
        movies = Movie.objects.all()
        for movie in movies:
            self.stdout.write(f"Movie: {movie.title}")
            self.stdout.write(f"Genres: {movie.genres}")
        
        unique_genres = set()
        for movie in movies:
            unique_genres.update(movie.genres)
        
        self.stdout.write("\nUnique genres:")
        for genre in sorted(unique_genres):
            self.stdout.write(genre)