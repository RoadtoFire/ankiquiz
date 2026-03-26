from rest_framework import filters, generics

from .models import Deck, Note
from .serializers import DeckSerializer, NoteListSerializer, NoteSerializer


class DeckListView(generics.ListAPIView):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer


class DeckDetailView(generics.RetrieveAPIView):
    queryset = Deck.objects.all()
    serializer_class = DeckSerializer


class NoteListView(generics.ListAPIView):
    serializer_class = NoteListSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['tags']

    def get_queryset(self):
        queryset = Note.objects.select_related('deck').all()

        # Filter by deck id
        deck_id = self.request.query_params.get('deck')
        if deck_id:
            queryset = queryset.filter(deck__id=deck_id)

        # Filter by has_images
        has_images = self.request.query_params.get('has_images')
        if has_images is not None:
            queryset = queryset.filter(has_images=has_images.lower() == 'true')

        return queryset


class NoteDetailView(generics.RetrieveAPIView):
    queryset = Note.objects.select_related('deck').prefetch_related('cards')
    serializer_class = NoteSerializer