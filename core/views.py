import csv
import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

CARD_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp'}
GENERAL_ASSET_DIRS = [
    ('A', 'card'),
    ('B', 'piece'),
    ('C', 'pieceHead'),
    ('D', 'broadcastGeneral'),
]


def _read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file, delimiter='\t')
        return [{k.strip(): (v or '').strip() for k, v in row.items() if k} for row in reader]


def _collect_card_assets() -> list[str]:
    card_dir = Path(settings.BASE_DIR) / 'assets' / 'card'
    if not card_dir.exists():
        return []

    result: list[str] = []
    for file in sorted(card_dir.iterdir()):
        if file.is_file() and file.suffix.lower() in CARD_SUFFIXES:
            result.append(f'assets/card/{file.name}')
    return result


def _build_general_handbook() -> list[dict[str, Any]]:
    configs_dir = Path(settings.BASE_DIR) / 'configs'
    rows = _read_tsv(configs_dir / 'card.csv') + _read_tsv(configs_dir / 'card_ex.csv')

    grouped: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        card_id = row.get('ID', '')
        card_type = row.get('类型', '')
        if not card_id or card_type not in {'1', '2'}:
            continue
        grouped.setdefault(card_id, {})[card_type] = {
            'id': card_id,
            'type': card_type,
            'name': row.get('名称', ''),
            'faction': row.get('势力', ''),
            'attack': row.get('攻击', ''),
            'health': row.get('血量', ''),
            'skill': row.get('技能描述', ''),
            'level': row.get('等级', ''),
        }

    all_items: list[dict[str, Any]] = []
    for atlas_code, atlas_dir in GENERAL_ASSET_DIRS:
        atlas_path = Path(settings.BASE_DIR) / 'assets' / atlas_dir
        if not atlas_path.exists():
            continue

        for img_file in sorted(atlas_path.iterdir()):
            if not img_file.is_file() or img_file.suffix.lower() not in CARD_SUFFIXES:
                continue

            card_id = img_file.stem
            versions = grouped.get(card_id, {})
            for card_type in ('1', '2'):
                version = versions.get(card_type)
                if not version:
                    continue
                all_items.append(
                    {
                        'atlas': atlas_code,
                        'atlasName': atlas_dir,
                        'image': f'assets/{atlas_dir}/{img_file.name}',
                        'version': version,
                    }
                )
    return all_items


def _build_spell_handbook() -> list[dict[str, str]]:
    rows = _read_tsv(Path(settings.BASE_DIR) / 'configs' / 'spell.csv')
    items: list[dict[str, str]] = []

    for row in rows:
        spell_id = row.get('ID', '')
        if not spell_id:
            continue
        items.append(
            {
                'id': spell_id,
                'image': f'assets/spell/{spell_id}.png',
                'name': row.get('名称', ''),
                'level': row.get('等级', ''),
                'skill': row.get('技能描述', ''),
            }
        )
    return items


def _build_weapon_handbook() -> list[dict[str, str]]:
    rows = _read_tsv(Path(settings.BASE_DIR) / 'configs' / 'weapon.csv')
    items: list[dict[str, str]] = []

    for row in rows:
        weapon_id = row.get('ID', '')
        if not weapon_id:
            continue
        items.append(
            {
                'id': weapon_id,
                'image': f'assets/weapon/{weapon_id}.png',
                'name': row.get('名称', ''),
                'type': row.get('类型', ''),
                'skill': row.get('技能描述', ''),
            }
        )
    return items


def game_view(request: HttpRequest) -> HttpResponse:
    card_paths = _collect_card_assets()
    handbook = {
        'generals': _build_general_handbook(),
        'spells': _build_spell_handbook(),
        'weapons': _build_weapon_handbook(),
    }
    return render(
        request,
        'game.html',
        {
            'card_paths_json': json.dumps(card_paths, ensure_ascii=False),
            'handbook_json': json.dumps(handbook, ensure_ascii=False),
        },
    )
