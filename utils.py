from .load_const import use_const
import uuid

def get_host(server, add_url):
    """Get the url from the config entry."""
    if use_const.MODE == "dev" or use_const.MODE == "dev_ha_real":
        return server
    return server + add_url

def get_hc_url(add_url):
    """Get the url from the config entry."""
    if use_const.MODE == "dev":
        return "http://127.0.0.1:8123"
    else:
        mac =  get_mac()
        base_url = f"https://{mac}.{add_url}"
    return base_url

def get_mac():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    mac_dec = int(mac, 16)
    return mac_dec
