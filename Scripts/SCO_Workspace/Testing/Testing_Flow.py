import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Add_item import add_item
from Components.Add_loyalty_card import add_loyalty_card
from Components.Redeem_choice_offer import redeem_choice_offer
from Components.Redeem_collectable_offer import redeem_collectable_offer
from Components.Promotion_details import get_promotion_details
from Components.Total_amount_details import get_total_amount_salemode, get_total_amount_tendermode, get_total_balancedue_tendermode
from Components.report import logger

tc_id = "TC_001"

logger.set_tc_id(tc_id)

try:

    add_item("9300677011523;9300677010670;9339687023882;9315087192083", "9355215896056")

    add_loyalty_card("9355215896056")

    # redeem_choice_offer("Market Day Mobile 10 percent off")

    total_amount = get_total_amount_tendermode()
    if float(total_amount) > 30:
        redeem_collectable_offer("Collectable", "You have earned.*Bricks Home packs, Are you collecting these? If yes, please call the attendant._No")

    get_promotion_details("")

except Exception as e:
    logger.log(f"Error: {e}", status="fail")
 
finally:
    logger.save()
    print(f"Report saved to {logger.report_path}")