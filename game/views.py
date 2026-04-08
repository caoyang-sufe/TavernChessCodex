from pathlib import Path

from django.conf import settings
from django.shortcuts import render


def game_view(request):
    card_dir = Path(settings.BASE_DIR) / 'assets' / 'card'
    card_paths = sorted(
        f"assets/card/{file_path.name}"
        for file_path in card_dir.glob('*.png')
        if file_path.is_file()
    )
    return render(request, 'game.html', {'card_paths': card_paths})
