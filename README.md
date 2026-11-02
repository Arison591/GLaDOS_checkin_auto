# GLaDOS 自动签到

基于 https://github.com/domeniczz/GLaDOS_checkin_auto 配置的 GitHub Actions 每日签到。

## 当前配置

- 每天北京时间 09:30（UTC 01:30）运行。GitHub 调度可能延迟。
- 可在 Actions → GLaDOS 每日签到 → Run workflow 手动执行。
- Cookie 只保存在仓库的 Actions secret 中，不写入代码。
- 当前账号使用 `glados.cloud`，已在仓库 Actions variable `GLADOS_BASE_URL` 中设为 `https://glados.cloud`。如果更换登录站点，请同步修改这个变量并重新获取对应站点的 Cookie。
- 请求使用 Windows Chrome 浏览器标识。如果以后改用其他设备登录，可在 Actions variable `GLADOS_USER_AGENT` 中填入登录浏览器的完整 User-Agent。
- 多个账号的 Cookie 使用 `&` 分隔。
- `PUSHPLUS_TOKEN` 为可选通知配置，不填写也能签到。
- 签到失败、Cookie 失效或网络异常时，任务会显示失败。

## 添加或更新 Cookie

1. 登录 https://glados.rocks/console/checkin 。
2. 按 F12 打开开发者工具，选择 Network（网络），刷新网页。
3. 选择发往 `glados.rocks/api/user/status` 的请求。
4. 在 Headers → Request Headers 中复制 `Cookie` 的完整值，不包含 `Cookie:`。
5. 打开本仓库 Settings → Secrets and variables → Actions。
6. 新增或更新名为 `GLADOS_COOKIE` 的 Repository secret，粘贴 Cookie。
7. 在 Actions 页面手动运行一次，查看“执行签到”的日志。

Cookie 过期后需要重复以上步骤。不要把 Cookie 提交到仓库、Issue 或日志中。

## GitHub 调度说明

公开仓库连续 60 天没有活动时，GitHub 可能自动停用定时工作流。
如发生停用，请在 Actions 页面重新启用，并手动运行一次。
原项目的第三方 keepalive 组件已被 GitHub 禁用，本配置已移除该依赖。

## 本地运行

需要 Python 3.10 或更新版本。安装依赖后，通过环境变量提供 Cookie：

```powershell
python -m pip install -r requirements.txt
# 在当前进程中设置 GLADOS_COOKIE，然后运行：
python glados.py
```

## 验证

```powershell
python -m unittest discover -s tests -v
```

青龙用户仍可使用原版的独立脚本 `glados_Qinglong.py`。
