"""GLaDOS check-in shared by GitHub Actions and local runs."""
import os
import re
import sys
from urllib.parse import urlsplit

import requests

BASE_URL = os.environ.get("GLADOS_BASE_URL", "https://glados.rocks").rstrip("/")
TIMEOUT = 30
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
)


def normalize_cookie(value):
    value = value.strip()
    value = re.sub(r"^cookie(?:\s*:\s*|\s*\r?\n\s*)", "", value, flags=re.IGNORECASE)
    return value.replace("\r", "").replace("\n", "").strip()


def checkin(cookie, number):
    headers = {
        "cookie": cookie,
        "referer": BASE_URL + "/console/checkin",
        "origin": BASE_URL,
        "user-agent": os.environ.get("GLADOS_USER_AGENT", "").strip() or DEFAULT_USER_AGENT,
    }
    try:
        response = requests.post(
            BASE_URL + "/api/user/checkin", headers=headers,
            json={"token": urlsplit(BASE_URL).hostname}, timeout=TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        response = requests.get(
            BASE_URL + "/api/user/status", headers=headers, timeout=TIMEOUT
        )
        response.raise_for_status()
        status = response.json()
        if not isinstance(result, dict) or not isinstance(status, dict):
            return False, f"账号 {number}：接口响应格式异常"
        data = status.get("data")
        if status.get("code") != 0 or not isinstance(data, dict) or "leftDays" not in data:
            return False, f"账号 {number}：无法读取账户状态，请检查或更新 GLADOS_COOKIE"
        message = str(result.get("message", "未返回签到结果"))
        # Code 1 can also mean an expired login: require an explicit duplicate message.
        already_checked = result.get("code") == 1 and (
            "checkin! Tomorrow" in message
            or "already checked in" in message.lower()
            or "checkin repeats" in message.lower()
            or "已经签到" in message
            or "已签到" in message
        )
        if result.get("code") != 0 and not already_checked:
            safe_message = message.replace(cookie, "[redacted]").replace("\r", " ").replace("\n", " ")[:200]
            return False, f"账号 {number}：签到未成功（code={result.get('code')}）：{safe_message}"
        days = str(data["leftDays"]).split(".")[0]
        return True, f"账号 {number}：{message}；剩余 {days} 天"
    except requests.RequestException as error:
        # Never print request objects or headers, which contain the cookie.
        detail = type(error).__name__
        if error.response is not None:
            detail += f" / HTTP {error.response.status_code}"
        return False, f"账号 {number}：请求失败（{detail}），请检查连接或 Cookie 格式"
    except (ValueError, TypeError):
        return False, f"账号 {number}：接口未返回有效 JSON，请稍后重试"


def main():
    cookies = [normalize_cookie(part) for part in os.environ.get("GLADOS_COOKIE", "").split("&") if part.strip()]
    if not cookies:
        print("未配置 GLADOS_COOKIE，请在 GitHub 仓库的 Actions secrets 中添加。")
        return 1
    messages = []
    success = True
    for number, cookie in enumerate(cookies, 1):
        ok, message = checkin(cookie, number)
        print(message)
        messages.append(message)
        success = success and ok
    token = os.environ.get("PUSHPLUS_TOKEN", "").strip()
    if token:
        try:
            response = requests.post(
                "https://www.pushplus.plus/send",
                json={
                    "token": token,
                    "title": "GLaDOS 签到结果" if success else "GLaDOS 签到异常",
                    "content": "\n".join(messages),
                    "template": "txt",
                }, timeout=TIMEOUT,
            )
            response.raise_for_status()
            if response.json().get("code") != 200:
                print("PushPlus 通知发送失败，请检查 PUSHPLUS_TOKEN。")
                success = False
        except (requests.RequestException, ValueError, AttributeError):
            print("PushPlus 通知发送失败，请检查网络和 PUSHPLUS_TOKEN。")
            success = False
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
