import csv
from pathlib import Path

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render

ROW_SIZE = 6
ROWS_PER_PAGE = 10
CARDS_PER_PAGE = ROW_SIZE * ROWS_PER_PAGE
TYPE_MAP = {'1': 'gold', '2': 'normal'}
TYPE_NAME_MAP = {'1': '金色版本', '2': '普通版本'}
CHINESE_NUMERAL = {1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六'}


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


def _read_tsv(relative_path: str):
    file_path = Path(settings.BASE_DIR) / relative_path
    with file_path.open('r', encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))



def _paginate(request, items, title: str, page_param: str, kind: str):
    paginator = Paginator(items, CARDS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get(page_param, 1))
    return {
        'title': title,
        'page_param': page_param,
        'page_obj': page_obj,
        'rows': _chunk_rows(list(page_obj.object_list), ROW_SIZE),
        'total': len(items),
        'kind': kind,
    }


def _build_general_items(asset_subdir: str):
    assets_dir = Path(settings.BASE_DIR) / 'assets' / asset_subdir
    records = _read_tsv('configs/card.csv') + _read_tsv('configs/card_ex.csv')
    items = []
    for row in records:
        card_id = row['ID']
        image_file = assets_dir / f'{card_id}.png'
        if not image_file.exists():
            continue
        card_type = row.get('类型', '').strip()
        level = int(row.get('等级', '1') or 1)
        items.append(
            {
                'image': f'{asset_subdir}/{card_id}.png',
                'name': row.get('名称', ''),
                'force': row.get('势力', ''),
                'attack': row.get('攻击', ''),
                'health': row.get('血量', ''),
                'skill': row.get('技能描述', ''),
                'level': level,
                'stars': '★' * max(1, min(6, level)),
                'type': TYPE_MAP.get(card_type, 'normal'),
                'type_name': TYPE_NAME_MAP.get(card_type, '普通版本'),
            }
        )
    return items


def _build_spell_items():
    assets_dir = Path(settings.BASE_DIR) / 'assets' / 'spell'
    items = []
    for row in _read_tsv('configs/spell.csv'):
        card_id = row['ID']
        image_file = assets_dir / f'{card_id}.png'
        if not image_file.exists():
            continue
        level = int(row.get('等级', '1') or 1)
        items.append(
            {
                'image': f'spell/{card_id}.png',
                'title': f"{row.get('名称', '')}·{CHINESE_NUMERAL.get(level, str(level))}",
                'skill': row.get('技能描述', ''),
            }
        )
    return items


def _build_weapon_items():
    assets_dir = Path(settings.BASE_DIR) / 'assets' / 'weapon'
    items = []
    for row in _read_tsv('configs/weapon.csv'):
        card_id = row['ID']
        image_file = assets_dir / f'{card_id}.png'
        if not image_file.exists():
            continue
        items.append(
            {
                'image': f'weapon/{card_id}.png',
                'name': row.get('名称', ''),
                'type_name': row.get('类型', ''),
                'skill': row.get('技能描述', ''),
            }
        )
    return items


def game_view(request):
    card_dir = Path(settings.BASE_DIR) / 'assets' / 'card'
    card_paths = sorted(
        f"card/{file_path.name}"
        for file_path in card_dir.glob('*.png')
        if file_path.is_file()
    )
    return render(request, 'game.html', {'card_paths': card_paths})


def handbook_view(request):
    sections = [
        _paginate(request, _build_general_items('card'), '武将图鉴 A（assets/card）', 'general_a_page', 'general'),
        _paginate(request, _build_general_items('piece'), '武将图鉴 B（assets/piece）', 'general_b_page', 'general'),
        _paginate(request, _build_general_items('pieceHead'), '武将图鉴 C（assets/pieceHead）', 'general_c_page', 'general'),
        _paginate(request, _build_general_items('broadcastGeneral'), '武将图鉴 D（assets/broadcastGeneral）', 'general_d_page', 'general'),
        _paginate(request, _build_spell_items(), '锦囊图鉴（assets/spell）', 'spell_page', 'spell'),
        _paginate(request, _build_weapon_items(), '装备图鉴（assets/weapon）', 'weapon_page', 'weapon'),
    ]
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
