app = None
win = None
current_user = ""
article_price = []
article_price_list = ""
article_name_list = ""
# article_qty_list = ""
is_loyaltycard_added = False
loyalty_points = 0
promotion_description_list = []
promotion_price_list = []
promotions_price = 0
total_promotions_price = 0.0
total_amount_salemode = 0
reward_redeem_status = False
redeem_amount = 0
total_amount_tendermode = 0
total_balancedue_tendermode = 0
ee_log_start_time = None  # Timestamp recorded before EE verification begins


def reset_state():
    """Reset all shared state before starting a new test run."""
    global app, win, current_user, article_price, article_price_list, article_name_list
    global is_loyaltycard_added, loyalty_points, promotion_description_list, promotion_price_list
    global promotions_price, total_promotions_price, total_amount_salemode, reward_redeem_status
    global redeem_amount, total_amount_tendermode, total_balancedue_tendermode, ee_log_start_time

    app = None
    win = None
    current_user = ""
    article_price = []
    article_price_list = ""
    article_name_list = ""
    is_loyaltycard_added = False
    loyalty_points = 0
    promotion_description_list = []
    promotion_price_list = []
    promotions_price = 0
    total_promotions_price = 0.0
    total_amount_salemode = 0
    reward_redeem_status = False
    redeem_amount = 0
    total_amount_tendermode = 0
    total_balancedue_tendermode = 0
    ee_log_start_time = None
    print("✅ Global state reset for new test run.")