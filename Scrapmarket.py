import time
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, LimitOrderArgs
from py_clob_client.order_builder.constants import BUY

# --- CONFIGURATION ---
HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  # Polygon Mainnet
PK = "YOUR_PRIVATE_KEY"
FUNDER = "YOUR_WALLET_ADDRESS"

# API Credentials (Generate these on Polymarket settings)
CREDS = ApiCreds(
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET",
    api_passphrase="YOUR_PASSPHRASE"
)

# Bot Parameters
SCAN_INTERVAL = 60  # seconds
PRICE_MIN = 0.01    # 1 cent
PRICE_MAX = 0.03    # 3 cents
DOWNSIDE_LIMIT = 2.0  # Risk $2 per trade

def get_yes_token_id(market):
    """Extracts the token ID for the 'YES' outcome from Gamma market data."""
    # Usually tokens[0] is YES, but checking 'outcome' label is safer
    for token in market.get('tokens', []):
        if token.get('outcome', '').upper() == 'YES':
            return token.get('token_id')
    return None

def run_bot():
    # Initialize CLOB Client
    client = ClobClient(HOST, key=PK, chain_id=CHAIN_ID, creds=CREDS)
    
    print("Bot started. Scanning for tail outcomes...")

    while True:
        try:
            # 1. Scan for all active markets via Gamma API
            # Note: For production, implement pagination for 'all' markets
            markets = client.get_simplified_markets().get('data', [])
            
            for market in markets:
                if not market.get('active'):
                    continue
                
                token_id = get_yes_token_id(market)
                if not token_id:
                    continue

                # 2. Check current price
                try:
                    # Fetching midpoint price as a proxy for market probability
                    price = float(client.get_price(token_id, side=BUY))
                except Exception:
                    continue

                # 3. Filter for Tail Outcomes (1-3 cents)
                if PRICE_MIN <= price <= PRICE_MAX:
                    # Calculate size based on $2 fixed downside
                    # Quantity = Total Investment / Price
                    quantity = DOWNSIDE_LIMIT / price
                    
                    print(f"Hunted Tail Outcome: {market.get('question')} @ {price*100}¢")
                    
                    # 4. Execute Buy Order
                    try:
                        resp = client.create_and_post_limit_order(
                            LimitOrderArgs(
                                price=price,
                                size=quantity,
                                side=BUY,
                                token_id=token_id
                            )
                        )
                        print(f"Order Placed: {resp}")
                    except Exception as e:
                        print(f"Trade failed: {e}")

            print(f"Scan complete. Sleeping for {SCAN_INTERVAL}s...")
            time.sleep(SCAN_INTERVAL)

        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_bot()
