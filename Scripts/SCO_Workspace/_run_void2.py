import sys
sys.path.insert(0, '.')
from Components.Login_POS import login_pos
from Components.Void_transaction import void_transaction

if not login_pos():
    raise SystemExit("login_pos failed")

result = void_transaction()
print("void_transaction result:", result)
