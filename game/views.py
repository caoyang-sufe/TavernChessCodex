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
    card_assets_dir = Path(settings.BASE_DIR) / 'assets' / 'card'
    spell_assets_dir = Path(settings.BASE_DIR) / 'assets' / 'spell'

    general_records = _read_tsv('configs/card.csv') + _read_tsv('configs/card_ex.csv')
    general_defs = []
    for row in general_records:
        if row.get('类型', '').strip() != '2':
            continue
        card_id = row.get('ID', '').strip()
        if not card_id:
            continue
        image_file = card_assets_dir / f'{card_id}.png'
        if not image_file.exists():
            continue
        level = int(row.get('等级', '1') or 1)
        general_defs.append(
            {
                'id': card_id,
                'kind': 'general',
                'path': f'card/{card_id}.png',
                'name': row.get('名称', card_id),
                'force': row.get('势力', ''),
                'attack': int(row.get('攻击', '0') or 0),
                'health': int(row.get('血量', '0') or 0),
                'skill': row.get('技能描述', ''),
                'level': level,
                'stars': '★' * max(1, min(6, level)),
                'type': 'normal',
            }
        )

    spell_defs = []
    for row in _read_tsv('configs/spell.csv'):
        spell_id = row.get('ID', '').strip()
        if not spell_id:
            continue
        image_file = spell_assets_dir / f'{spell_id}.png'
        if not image_file.exists():
            continue
        level = int(row.get('等级', '1') or 1)
        spell_defs.append(
            {
                'id': spell_id,
                'kind': 'spell',
                'path': f'spell/{spell_id}.png',
                'name': row.get('名称', spell_id),
                'skill': row.get('技能描述', ''),
                'level': level,
                'title': f"{row.get('名称', spell_id)}·{CHINESE_NUMERAL.get(level, str(level))}",
            }
        )

    return render(
        request,
        'game.html',
        {
            'card_defs': general_defs,
            'spell_defs': spell_defs,
            'skill_terms': _read_entry_terms(),
        },
    )


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
