from access_control_api import AccessControlAPI

# Initialize
api = AccessControlAPI("https://residential_tirumala_zero.easyslot.in", "your-api-key-change-this")
api.login("admin", "admin123")

# Get all users
users = api.get_users()
for user in users:
    print(f"{user['name']}: {user['card_number']}")

# Add user
# api.add_user("12345678", "USR001", "John Doe", "EMP123")
# api.delete_user("12345678")
# Control relay (open door 1)
# api.pulse_relay(1)

# Block user
# api.block_user("12345678")

# Get analytics
# analytics = api.get_analytics(days=30)
# print(f"Total transactions: {analytics['total_transactions']}")

# Get transactions
transactions = api.get_transactions(limit=50)

# Download CSV
# csv = api.download_transactions_csv(limit=500)
# with open("export.csv", "w") as f:
#     f.write(csv)

# Logout
api.logout()
