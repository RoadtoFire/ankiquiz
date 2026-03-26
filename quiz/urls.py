from django.urls import path

from .views import DeckDetailView, DeckListView, NoteDetailView, NoteListView

urlpatterns = [
    path('decks/', DeckListView.as_view(), name='deck-list'),
    path('decks/<int:pk>/', DeckDetailView.as_view(), name='deck-detail'),
    path('notes/', NoteListView.as_view(), name='note-list'),
    path('notes/<int:pk>/', NoteDetailView.as_view(), name='note-detail'),
]