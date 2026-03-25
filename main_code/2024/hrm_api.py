import aiohttp
import logging
import time
from .const import HRM_CLIENT_ID, HRM_CLIENT_SECRET, HRM_TOKEN_URL, HRM_QUEUE_URL, HRM_ACK_URL

LOGGER = logging.getLogger(__name__)

class HRMClient:
    def __init__(self):
        self.client_id = HRM_CLIENT_ID
        self.client_secret = HRM_CLIENT_SECRET
        self.access_token = None
        self.token_expires_at = 0

    async def get_token(self):
        """Lấy access token mới hoặc trả về token hiện tại nếu chưa hết hạn."""
        # Làm mới nếu token hết hạn trong chưa đầy 60 giây
        if self.access_token and time.time() < self.token_expires_at - 60:
            return self.access_token

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        headers = {"Content-Type": "application/json"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(HRM_TOKEN_URL, json=payload, headers=headers) as response:
                    if response.status == 200:
                        res = await response.json()
                        token_data = res.get("data", {})
                        self.access_token = token_data.get("access_token")
                        expires_in = token_data.get("expires_in", 3600)
                        self.token_expires_at = time.time() + expires_in
                        LOGGER.info("Successfully fetched new HRM access token.")
                        return self.access_token
                    else:
                        LOGGER.error(f"Failed to fetch HRM token. Status: {response.status}")
                        return None
        except Exception as e:
            LOGGER.error(f"Exception fetching HRM token: {e}")
            return None

    async def fetch_queue(self, place_id, limit=50):
        """Lấy danh sách hàng đợi từ HRM."""
        token = await self.get_token()
        if not token:
            return None

        url = f"{HRM_QUEUE_URL}?place_id={place_id}&limit={limit}"
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        return res_json.get("data", [])
                    else:
                        text = await response.text()
                        LOGGER.error(f"Failed to fetch HRM queue. Status: {response.status}, Response: {text}")
                        return []
        except Exception as e:
            LOGGER.error(f"Exception fetching HRM queue: {e}")
            return None

    async def ack_queue(self, results):
        """Phản hồi kết quả xử lý hàng đợi về HRM."""
        if not results:
            return True
            
        token = await self.get_token()
        if not token:
            return False
            
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"results": results}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(HRM_ACK_URL, json=payload, headers=headers) as response:
                    if response.status == 200:
                        LOGGER.info(f"Successfully ACKed {len(results)} queue items.")
                        return True
                    else:
                        text = await response.text()
                        LOGGER.error(f"Failed to ACK HRM queue. Status: {response.status}, Response: {text}")
                        return False
        except Exception as e:
            LOGGER.error(f"Exception ACKing HRM queue: {e}")
            return False
