# TavernChessCodex

一个战棋酒馆原型项目，使用 Django 后端动态加载 `assets` 下的卡牌素材。

## 启动方式

1. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

2. 启动开发服务器：

   ```bash
   python manage.py runserver
   ```

3. 浏览器访问：

   - `http://127.0.0.1:8000/`

## 关键说明

- `game.html` 作为 Django 模板放在 `templates/game.html`。
- 后端视图 `game/views.py` 会扫描 `./assets/card/*.png`，动态生成卡牌路径列表。
- 模板通过 `json_script` 注入 `card_paths`，前端脚本不再硬编码卡牌数组。
- 静态资源通过 Django `staticfiles` 提供，访问前缀为 `/static/`。
