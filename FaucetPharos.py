import requests
import json
import time
import sys
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
import os
from colorama import init, Fore, Style

init()

# Configuration
WEB3_PROVIDER = "https://testnet.dplabs-internal.com"
FAUCET_URL = "https://api.pharosnetwork.xyz/faucet/daily"
LOGIN_URL = "https://api.pharosnetwork.xyz/user/login"
INVITE_CODE = "jUSO6Lgq2zUHcFEx"
WALLET_FILE = "wallet.txt"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "ja-ID,ja;q=0.9,id-ID;q=0.8,id;q=0.7,en-ID;q=0.6,en-US;q=0.5,en;q=0.4",
    "Origin": "https://testnet.pharosnetwork.xyz",
    "Referer": "https://testnet.pharosnetwork.xyz/",
    "Sec-Ch-Ua": '"Chromium";v="137", "Not/A)Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?1",
    "Sec-Ch-Ua-Platform": '"Android"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36"
}

w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

# Fancy Banner
BANNER = f"""
{Fore.CYAN}{Style.BRIGHT}🌠 PHAROS Fucet Fuck BOT - By poopbots Auto Claim & Transfer 🌠
{Fore.YELLOW}═══════════════════════════════════════════════
{Fore.GREEN}🚀 Automates Pharos Fuck faucet claims
{Fore.GREEN}💸 Transfers to single wallet from {WALLET_FILE}
{Fore.BLUE}👨‍💻 Developed by: Poopbot Enjoy 
{Fore.YELLOW}═══════════════════════════════════════════════{Style.RESET_ALL}
"""

# Text-based progress bar animation
def progress_bar_animation(message, duration):
    bar_length = 20
    end_time = time.time() + duration
    while time.time() < end_time:
        for i in range(bar_length + 1):
            progress = "█" * i + " " * (bar_length - i)
            sys.stdout.write(f'\r{Fore.YELLOW}{message} [{progress}] {i*5}%{Style.RESET_ALL}')
            sys.stdout.flush()
            time.sleep(duration / bar_length)
    sys.stdout.write(f'\r{Fore.YELLOW}{message} [█{'█' * bar_length}] 100% Done!{Style.RESET_ALL}\n')
    sys.stdout.flush()

def check_rpc_connection():
    print(f"{Fore.BLUE}🔍 Checking RPC connection...{Style.RESET_ALL}")
    try:
        if w3.is_connected():
            print(f"{Fore.GREEN}✅ Connected to RPC: {WEB3_PROVIDER}{Style.RESET_ALL}")
            return True
        else:
            print(f"{Fore.RED}❌ Failed to connect to RPC: {WEB3_PROVIDER}{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ Error checking RPC: {str(e)}{Style.RESET_ALL}")
        return False

def generate_wallet():
    account = Account.create()
    address = account.address
    private_key = account._private_key.hex()
    return address, private_key

def create_signature(private_key, message="pharos"):
    try:
        account = w3.eth.account.from_key(private_key)
        message_hash = encode_defunct(text=message)
        signed_message = w3.eth.account.sign_message(message_hash, private_key=private_key)
        return signed_message.signature.hex(), account.address
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to create signature: {str(e)}{Style.RESET_ALL}")
        return None, None

def login(address, signature, retries=3):
    login_params = {
        "address": address,
        "signature": signature,
        "invite_code": INVITE_CODE
    }
    
    for attempt in range(retries):
        try:
            response = requests.post(LOGIN_URL, headers=HEADERS, params=login_params)
            if response.status_code == 200 and response.json().get("code") == 0:
                print(f"{Fore.GREEN}✅ Login successful for {address}{Style.RESET_ALL}")
                return response.json().get("data").get("jwt")
            print(f"{Fore.RED}❌ Login failed (Attempt {attempt+1}/{retries}): {response.json()}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Login failed (Attempt {attempt+1}/{retries}): {str(e)}{Style.RESET_ALL}")
        
        if attempt < retries - 1:
            progress_bar_animation("⏳ Retrying login...", 2)
    
    print(f"{Fore.RED}❌ Login failed after {retries} attempts{Style.RESET_ALL}")
    return None

def claim_faucet(address, private_key):
    signature, recovered_address = create_signature(private_key)
    if not signature or recovered_address.lower() != address.lower():
        print(f"{Fore.RED}❌ Failed to create signature or address mismatch{Style.RESET_ALL}")
        return False
    
    jwt = login(address, signature)
    if not jwt:
        print(f"{Fore.RED}❌ Login failed{Style.RESET_ALL}")
        return False
    
    headers = HEADERS.copy()
    headers["Authorization"] = f"Bearer {jwt}"
    
    for attempt in range(3):
        try:
            response = requests.post(f"{FAUCET_URL}?address={address}", headers=headers)
            if response.status_code == 200:
                print(f"{Fore.GREEN}✅ Successfully claimed faucet for {address}{Style.RESET_ALL}")
                return True
            print(f"{Fore.RED}❌ Failed to claim faucet (Attempt {attempt+1}/3): {response.json()}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to claim faucet (Attempt {attempt+1}/3): {str(e)}{Style.RESET_ALL}")
        
        if attempt < 2:
            progress_bar_animation("⏳ Retrying faucet claim...", 2)
    
    print(f"{Fore.RED}❌ Failed to claim faucet after 3 attempts{Style.RESET_ALL}")
    return False

def get_balance(address):
    try:
        balance_wei = w3.eth.get_balance(address)
        balance_phrs = w3.from_wei(balance_wei, "ether")
        return balance_wei, balance_phrs
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to get balance for {address}: {str(e)}{Style.RESET_ALL}")
        return 0, 0

def transfer_peach(private_key, to_address, amount_wei):
    try:
        account = w3.eth.account.from_key(private_key)
        from_address = account.address
        
        nonce = w3.eth.get_transaction_count(from_address, "pending")
        gas_price = w3.eth.gas_price
        gas_limit = 21000
        
        tx = {
            "from": from_address,
            "to": to_address,
            "value": amount_wei,
            "gas": gas_limit,
            "gasPrice": gas_price,
            "nonce": nonce,
            "chainId": 688688
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            print(f"{Fore.GREEN}✅ Tx Hash: {w3.to_hex(tx_hash)}{Style.RESET_ALL}")
            progress_bar_animation("⏳ Processing transaction...", 3)
            return True
        else:
            print(f"{Fore.RED}❌ Transfer failed for {from_address}{Style.RESET_ALL}")
            progress_bar_animation("⏳ Waiting before retry...", 3)
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ Failed to transfer from {from_address}: {str(e)}{Style.RESET_ALL}")
        progress_bar_animation("⏳ Waiting before retry...", 3)
        return False

def is_valid_address(address):
    return w3.is_address(address)

def read_wallet_address():
    try:
        if not os.path.exists(WALLET_FILE):
            print(f"{Fore.RED}❌ {WALLET_FILE} not found! Please create it with a valid Ethereum address.{Style.RESET_ALL}")
            return None
        with open(WALLET_FILE, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
            if not lines:
                print(f"{Fore.RED}❌ {WALLET_FILE} is empty! Please add a valid Ethereum address.{Style.RESET_ALL}")
                return None
            address = lines[0]  # Use the first address
            if is_valid_address(address):
                return w3.to_checksum_address(address)
            else:
                print(f"{Fore.RED}❌ Invalid address in {WALLET_FILE}: {address}{Style.RESET_ALL}")
                return None
    except Exception as e:
        print(f"{Fore.RED}❌ Error reading {WALLET_FILE}: {str(e)}{Style.RESET_ALL}")
        return None

def get_cycle_count():
    while True:
        try:
            cycles = int(input(f"{Fore.YELLOW}🔢 Enter the number of cycles (each cycle creates 10 wallets): {Style.RESET_ALL}"))
            if cycles <= 0:
                print(f"{Fore.RED}❌ Number of cycles must be greater than 0{Style.RESET_ALL}")
                continue
            print(f"{Fore.GREEN}✅ Will run {cycles} cycles with 10 wallets each{Style.RESET_ALL}")
            return cycles
        except ValueError:
            print(f"{Fore.RED}❌ Please enter a valid number{Style.RESET_ALL}")

def process_batch(recipient, batch_size=10):
    wallets = []
    
    print(f"{Fore.CYAN}🌟 Creating {batch_size} new wallets...{Style.RESET_ALL}")
    progress_bar_animation("⏳ Generating wallets...", 2)
    for _ in range(batch_size):
        address, private_key = generate_wallet()
        wallets.append((address, private_key))
        print(f"{Fore.BLUE}🆕 New wallet created - Address: {address}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}🔑 Logging in for {batch_size} wallets...{Style.RESET_ALL}")
    progress_bar_animation("⏳ Processing logins...", 2)
    for i, (address, private_key) in enumerate(wallets[:]):
        signature, recovered_address = create_signature(private_key)
        if signature and recovered_address.lower() == address.lower():
            jwt = login(address, signature)
            if jwt:
                wallets[i] = (address, private_key, jwt)
            else:
                print(f"{Fore.RED}❌ Login failed for {address}, skipping this wallet{Style.RESET_ALL}")
                wallets[i] = None
        else:
            print(f"{Fore.RED}❌ Failed to create signature for {address}, skipping this wallet{Style.RESET_ALL}")
            wallets[i] = None
    
    print(f"{Fore.CYAN}💧 Claiming faucet for wallets that logged in successfully...{Style.RESET_ALL}")
    progress_bar_animation("⏳ Claiming faucets...", 2)
    for i, wallet in enumerate(wallets[:]):
        if wallet is None:
            continue
        address, private_key, jwt = wallet
        headers = HEADERS.copy()
        headers["Authorization"] = f"Bearer {jwt}"
        try:
            response = requests.post(f"{FAUCET_URL}?address={address}", headers=headers)
            if response.status_code == 200:
                print(f"{Fore.GREEN}✅ Successfully claimed faucet for {address}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Failed to claim faucet for {address}: {response.json()}{Style.RESET_ALL}")
                wallets[i] = None
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to claim faucet for {address}: {str(e)}{Style.RESET_ALL}")
            wallets[i] = None
    
    print(f"{Fore.CYAN}💸 Transferring to {recipient}...{Style.RESET_ALL}")
    progress_bar_animation("⏳ Initiating transfers...", 2)
    for wallet in wallets:
        if wallet is None:
            continue
        address, private_key, _ = wallet
        balance_wei, balance_phrs = get_balance(address)
        print(f"{Fore.BLUE}💰 Balance {address}: {balance_phrs:.4f} PHRS{Style.RESET_ALL}")
        
        if balance_wei == 0:
            print(f"{Fore.RED}❌ Zero balance for {address}, skipping this wallet{Style.RESET_ALL}")
            continue
        
        gas_limit = 21000
        gas_price = w3.eth.gas_price
        gas_fee = gas_limit * gas_price
        
        if balance_wei <= gas_fee:
            print(f"{Fore.RED}❌ Insufficient balance for gas in {address}, skipping this wallet{Style.RESET_ALL}")
            continue
        
        amount_wei = balance_wei - gas_fee
        if amount_wei <= 0:
            print(f"{Fore.RED}❌ Invalid transfer amount for {address}, skipping this wallet{Style.RESET_ALL}")
            continue
        
        if transfer_peach(private_key, recipient, amount_wei):
            print(f"{Fore.GREEN}✅ Successfully transferred from {address} to {recipient}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Failed to transfer from {address}{Style.RESET_ALL}")

def main():
    print(BANNER)
    
    if not check_rpc_connection():
        print(f"{Fore.RED}❌ Cannot proceed due to RPC connection issue{Style.RESET_ALL}")
        return
    
    # Read single recipient address from wallet.txt
    recipient = read_wallet_address()
    if not recipient:
        print(f"{Fore.RED}❌ Cannot proceed without a valid recipient address in {WALLET_FILE}{Style.RESET_ALL}")
        return
    
    print(f"{Fore.GREEN}✅ Using recipient address: {recipient} for all cycles{Style.RESET_ALL}")
    
    total_cycles = get_cycle_count()
    
    for cycle in range(1, total_cycles + 1):
        print(f"{Fore.CYAN}🌌 Starting Cycle {cycle} of {total_cycles} 🌌{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}💸 Processing 10 claims and transferring to {recipient}{Style.RESET_ALL}")
        process_batch(recipient)
        
        print(f"{Fore.GREEN}✅ Completed Cycle {cycle}: Processed 10 claims and transfers!{Style.RESET_ALL}")
        if cycle < total_cycles:
            progress_bar_animation("⏳ Waiting for next cycle...", 10)
    
    print(f"{Fore.GREEN}🎉 All {total_cycles} cycles completed successfully!{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
