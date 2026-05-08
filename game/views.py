import csv
import re
from pathlib import Path

from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils.html import escape
from django.utils.safestring import mark_safe

ROW_SIZE = 6
ROWS_PER_PAGE = 10
CARDS_PER_PAGE = ROW_SIZE * ROWS_PER_PAGE
TYPE_MAP = {'1': 'gold', '2': 'normal'}
TYPE_NAME_MAP = {'1': '金色版本', '2': '普通版本'}
CHINESE_NUMERAL = {1: '一', 2: '二', 3: '三', 4: '四', 5: '五', 6: '六'}


def _static_url(relative_path: str):
    return f"{settings.STATIC_URL}{relative_path}"


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


def _read_entry_terms():
    rows = _read_tsv('configs/entry_desc.csv')
    terms = [row.get('词条', '').strip() for row in rows if row.get('词条', '').strip()]
    return sorted(set(terms), key=len, reverse=True)


def _highlight_skill_text(text: str, terms_pattern: re.Pattern):
    escaped = escape(text or '')
    if not escaped:
        return mark_safe('')

    highlighted = terms_pattern.sub(
        lambda match: f'<span class="skill-term">{match.group(0)}</span>',
        escaped,
    )
    return mark_safe(highlighted)


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


def _build_general_items(asset_subdir: str, terms_pattern: re.Pattern):
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
        skill_text = row.get('技能描述', '')
        items.append(
            {
                'image': f'{asset_subdir}/{card_id}.png',
                'image_url': _static_url(f'{asset_subdir}/{card_id}.png'),
                'name': row.get('名称', ''),
                'force': row.get('势力', ''),
                'attack': row.get('攻击', ''),
                'health': row.get('血量', ''),
                'skill': skill_text,
                'skill_html': _highlight_skill_text(skill_text, terms_pattern),
                'level': level,
                'stars': '★' * max(1, min(6, level)),
                'type': TYPE_MAP.get(card_type, 'normal'),
                'type_name': TYPE_NAME_MAP.get(card_type, '普通版本'),
            }
        )
    return items


def _build_spell_items(terms_pattern: re.Pattern):
    assets_dir = Path(settings.BASE_DIR) / 'assets' / 'spell'
    items = []
    for row in _read_tsv('configs/spell.csv'):
        card_id = row['ID']
        image_file = assets_dir / f'{card_id}.png'
        if not image_file.exists():
            continue
        level = int(row.get('等级', '1') or 1)
        skill_text = row.get('技能描述', '')
        items.append(
            {
                'image': f'spell/{card_id}.png',
                'image_url': _static_url(f'spell/{card_id}.png'),
                'title': f"{row.get('名称', '')}·{CHINESE_NUMERAL.get(level, str(level))}",
                'skill': skill_text,
                'skill_html': _highlight_skill_text(skill_text, terms_pattern),
            }
        )
    return items


def _build_weapon_items(terms_pattern: re.Pattern):
    assets_dir = Path(settings.BASE_DIR) / 'assets' / 'weapon'
    items = []
    for row in _read_tsv('configs/weapon.csv'):
        card_id = row['ID']
        image_file = assets_dir / f'{card_id}.png'
        if not image_file.exists():
            continue
        skill_text = row.get('技能描述', '')
        items.append(
            {
                'image': f'weapon/{card_id}.png',
                'image_url': _static_url(f'weapon/{card_id}.png'),
                'name': row.get('名称', ''),
                'type_name': row.get('类型', ''),
                'skill': skill_text,
                'skill_html': _highlight_skill_text(skill_text, terms_pattern),
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
    shop_rows = _read_tsv('configs/card.csv')
    derived_rows = _read_tsv('configs/card_ex.csv')
    game_cards = []

    for row in shop_rows:
        card_id = row.get('ID', '').strip()
        if not card_id:
            continue
        image_path = f'card/{card_id}.png'
        if image_path not in card_paths:
            continue
        game_cards.append(
            {
                'id': card_id,
                'path': image_path,
                'name': row.get('名称', ''),
                'type': row.get('类型', '2'),
                'force': row.get('势力', ''),
                'level': int(row.get('等级', '1') or 1),
                'attack': int(row.get('攻击', '0') or 0),
                'health': int(row.get('血量', '0') or 0),
                'skill': row.get('技能描述', ''),
                'is_derived': False,
            }
        )

    for row in derived_rows:
        card_id = row.get('ID', '').strip()
        if not card_id:
            continue
        image_path = f'card/{card_id}.png'
        if image_path not in card_paths:
            continue
        game_cards.append(
            {
                'id': card_id,
                'path': image_path,
                'name': row.get('名称', ''),
                'type': row.get('类型', '2'),
                'force': row.get('势力', ''),
                'level': int(row.get('等级', '1') or 1),
                'attack': int(row.get('攻击', '0') or 0),
                'health': int(row.get('血量', '0') or 0),
                'skill': row.get('技能描述', ''),
                'is_derived': True,
            }
        )

    return render(request, 'game.html', {'card_paths': card_paths, 'game_cards': game_cards})


def handbook_view(request):
    entry_terms = _read_entry_terms()
    if entry_terms:
        terms_pattern = re.compile('|'.join(re.escape(term) for term in entry_terms))
    else:
        terms_pattern = re.compile(r'^(?!)')

    sections = [
        _paginate(request, _build_general_items('card', terms_pattern), '武将图鉴 A（assets/card）', 'general_a_page', 'general'),
        _paginate(request, _build_general_items('piece', terms_pattern), '武将图鉴 B（assets/piece）', 'general_b_page', 'general'),
        _paginate(request, _build_general_items('pieceHead', terms_pattern), '武将图鉴 C（assets/pieceHead）', 'general_c_page', 'general'),
        _paginate(request, _build_general_items('broadcastGeneral', terms_pattern), '武将图鉴 D（assets/broadcastGeneral）', 'general_d_page', 'general'),
        _paginate(request, _build_spell_items(terms_pattern), '锦囊图鉴（assets/spell）', 'spell_page', 'spell'),
        _paginate(request, _build_weapon_items(terms_pattern), '装备图鉴（assets/weapon）', 'weapon_page', 'weapon'),
    ]
    return render(request, 'handbook.html', {'sections': sections})
