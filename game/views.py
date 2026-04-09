from pathlib import Path

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render

ROW_SIZE = 6
ROWS_PER_PAGE = 10
CARDS_PER_PAGE = ROW_SIZE * ROWS_PER_PAGE


def _list_images(relative_dir: str):
    target_dir = Path(settings.BASE_DIR) / 'assets' / relative_dir
    return sorted(
        f"{relative_dir}/{file_path.name}"
        for file_path in target_dir.glob('*.png')
        if file_path.is_file()
    )


def _chunk_rows(items, row_size: int = ROW_SIZE, rows_per_page: int = ROWS_PER_PAGE):
    rows = [items[index:index + row_size] for index in range(0, len(items), row_size)]
    rows = rows[:rows_per_page]
    while len(rows) < rows_per_page:
        rows.append([])
    return [row + [None] * (row_size - len(row)) for row in rows]


def game_view(request):
    card_paths = _list_images('card')
    return render(request, 'game.html', {'card_paths': card_paths})


def handbook_view(request):
    catalogs = {
        'general': {
            'title': '武将卡牌图鉴',
            'items': _list_images('card'),
            'page_param': 'general_page',
        },
        'spell': {
            'title': '锦囊卡牌图鉴',
            'items': _list_images('spell'),
            'page_param': 'spell_page',
        },
        'weapon': {
            'title': '装备卡牌图鉴',
            'items': _list_images('weapon'),
            'page_param': 'weapon_page',
        },
    }

    sections = []
    for key, config in catalogs.items():
        paginator = Paginator(config['items'], CARDS_PER_PAGE)
        page_number = request.GET.get(config['page_param'], 1)
        page_obj = paginator.get_page(page_number)
        rows = _chunk_rows(list(page_obj.object_list), ROW_SIZE)
        sections.append(
            {
                'key': key,
                'title': config['title'],
                'page_param': config['page_param'],
                'page_obj': page_obj,
                'rows': rows,
                'total': len(config['items']),
            }
        )

    return render(request, 'handbook.html', {'sections': sections})
