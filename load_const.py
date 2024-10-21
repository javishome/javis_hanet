from .const import const
from .const import const_dev
from .const import const_dev_ha_real
# mode = "dev_ha_real"
# mode = "dev"
mode = "prod"
def load_const():
    if mode == "dev":
        return const_dev
    elif mode == "dev_ha_real":
        return const_dev_ha_real
    return const

use_const = load_const()