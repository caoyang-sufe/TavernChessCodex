import json
from pathlib import Path

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


CARD_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp'}


def _collect_card_assets() -> list[str]:
    card_dir = Path(settings.BASE_DIR) / 'assets' / 'card'
    if not card_dir.exists():
        return []

    result: list[str] = []
    for file in sorted(card_dir.iterdir()):
        if file.is_file() and file.suffix.lower() in CARD_SUFFIXES:
            result.append(f'assets/card/{file.name}')
    return result


def game_view(request: HttpRequest) -> HttpResponse:
    card_paths = _collect_card_assets()
    return render(
        request,
        'game.html',
        {
            'card_paths_json': json.dumps(card_paths, ensure_ascii=False),
        },
    )
