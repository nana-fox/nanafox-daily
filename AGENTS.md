# 日报网站

- 正式入口为 `https://nanafox.com/daily/`，BASE_PATH 保持 `/daily`。Pages `nanafox-daily` 从 main 的 dist 自动发布，提交前运行 `python3 scripts/build_site.py`。
- Grok 继续负责采集、筛选和生成 JSON/PNG。此仓库只负责网站模板与发布，不要重写上游生成流程。
- 网页先展示今日要点和分类摘要，长图默认折叠，下载入口保留。
- 构建必须生成 `/daily/latest.json`，格式 `{date, title, url, tldr: [{title, text}]}`；官网首页只展示固定介绍，不依赖这一接口。
- 保留完整需要公开的历史 JSON/PNG；构建器会重建 dist。运行 `python3 -m unittest discover -s tests -v` 后再发布。
- 官网 Worker 在 nanafox-landing 仓库维护，不修改官网以外的业务 DNS。密钥不进入仓库。

- 新版界面源码在 web/，已编译资源在 site/reader/。修改前端后运行 `npm --prefix web test`、`npm --prefix web run build`，再运行 Python 构建与测试；日常数据更新直接运行 Python，无需 Node。源码与编译产物必须同时提交。
- 导出绑定当前完整一期；JSON 保持原始结构，图片包含完整要点与分类正文，分页不可截断正文。
