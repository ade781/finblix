import httpx
from typing import Dict, Any

class WebhookService:
    @staticmethod
    async def send_discord_alert(webhook_url: str, message: str) -> Dict[str, Any]:
        if not webhook_url:
            return {"status": "error", "message": "URL Webhook Discord kosong"}

        payload = {
            "content": f"🚨 **FINBLIX MARKET ALERT**\n{message}"
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(webhook_url, json=payload)
                if res.status_code in [200, 204]:
                    return {"status": "success", "message": "Notifikasi berhasil dikirim ke Discord!"}
                else:
                    return {"status": "error", "message": f"Discord merespon dengan status code {res.status_code}"}
        except Exception as e:
            return {"status": "error", "message": f"Gagal menghubungi Discord: {str(e)}"}

    @staticmethod
    async def send_telegram_alert(bot_token: str, chat_id: str, message: str) -> Dict[str, Any]:
        if not bot_token or not chat_id:
            return {"status": "error", "message": "Bot Token atau Chat ID Telegram kosong"}

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"🚨 FINBLIX MARKET ALERT\n\n{message}",
            "parse_mode": "Markdown"
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    return {"status": "success", "message": "Notifikasi berhasil dikirim ke Telegram!"}
                else:
                    return {"status": "error", "message": f"Telegram merespon: {res.text}"}
        except Exception as e:
            return {"status": "error", "message": f"Gagal menghubungi Telegram: {str(e)}"}
