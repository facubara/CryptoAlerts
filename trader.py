import http
import json
from dotenv import load_dotenv
from colorama import Fore, Style, init
import os
import requests
from solders.keypair import Keypair

sol_address = "So11111111111111111111111111111111111111112"
giga_address = "63LfDmNb3MQ8mw9MtZ2To9bEA2M71kZUUGq5tiJxcqj9"

def get_quote(input_mint: str, output_mint: str, amount: int, slippage_bps: int):
    try:
        # url = "https://quote-api.jup.ag/v6/quote"
        url = "https://api.jup.ag/swap/v1/quote"
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': amount,
            'slippageBps': slippage_bps,
            'onlyDirectRoutes': 'true'
            # 'restrictIntermediateTokens': 'false'
        }
        headers = {'Accept': 'application/json'}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error in get_quote: {e}")
        return None

def send_swap(quote, publicKey):
    conn = http.client.HTTPSConnection("api.jup.ag")
    payload = json.dumps({"userPublicKey": publicKey,
                          "quoteResponse": quote,
                          "prioritizationFeeLamports": 
                            {
                            "priorityLevelWithMaxLamports": 
                                {
                                    "maxLamports": 10000000,
                                    "priorityLevel": "veryHigh"
                                }
                            },
                        "dynamicComputeUnitLimit": True
                         })
    headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
    }
    print(payload)
    conn.request("POST", "/swap/v1/swap", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


if __name__ == "__main__":
    load_dotenv()
    PUB_KEY = os.getenv('PUB_KEY')
    PRIV_KEY = os.getenv('PRIV_KEY')
    quoteresponse = get_quote("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", giga_address, 10000, 2)
    # print(quoteresponse)
    send_swap(quoteresponse, PUB_KEY)

    # payer_keypair = Keypair.from_base58_string(PRIV_KEY)