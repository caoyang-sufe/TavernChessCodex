# TavernChessCodex

一个战棋酒馆原型项目，现已增加 Django 后端用于动态加载卡牌素材。

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

- `game.html` 已迁移为 Django 模板：`core/templates/game.html`。
- 后端会扫描 `./assets/card` 目录，动态生成 `cardPaths` 给前端脚本使用。
- 静态资源通过 Django `staticfiles` 提供，URL 前缀为 `/assets/`。
