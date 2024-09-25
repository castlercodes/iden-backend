# node_communication.py

import requests
from config import AUTHORITY_NODE_URL

def add_node(node_address):
    payload = {'node_address': node_address}
    response = requests.post(f'{AUTHORITY_NODE_URL}/add_node', json=payload)
    print(response.json())

def sync_blockchain():
    response = requests.get(f'{AUTHORITY_NODE_URL}/sync_blockchain')
    chain = response.json()
    print("Synchronized blockchain:", chain)

def broadcast_block(peer_nodes, block):
    block_data = {
        'previous_hash': block.previous_hash,
        'transaction': block.transaction,
        'timestamp': block.timestamp,
        'hash': block.hash
    }
    for node in peer_nodes:
        try:
            response = requests.post(f'http://{node}/receive_block', json=block_data)
            if response.status_code == 200:
                print(f"Block broadcasted to {node}")
            else:
                print(f"Failed to broadcast block to {node}")
        except requests.exceptions.RequestException as e:
            print(f"Error broadcasting to {node}: {e}")
