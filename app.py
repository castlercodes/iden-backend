from flask import Flask, request, jsonify
from blockchain import Blockchain, Block
from node_communication import broadcast_block
import random
import jwt
import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST"], "allow_headers": "*"}})

blockchain = Blockchain()
peer_nodes = []
user_db = {}
issued_tokens = {}
p = 29
g = 5
SECRET_KEY = "secret-key-for-tokens" 

def mod_exp(base, exp, mod):
    return pow(base, exp, mod)

def verify_proof(s, T, C, c):
    left_hand_side = mod_exp(g, s, p)
    right_hand_side = (T * mod_exp(C, c, p)) % p
    return left_hand_side == right_hand_side

def challenge_verifier(q):
    return random.randint(1, q - 1)

def issue_token(user_id, node_id):
    token = jwt.encode({
        "user_id": user_id,
        "node_id": node_id,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5),
    }, SECRET_KEY, algorithm="HS256")
    return token

def verify_token(token):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded_token
    except jwt.ExpiredSignatureError:
        return None

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user_id = data['userId']
    fingerprint_hash = data['hashedPassword']

    for block in blockchain.chain:
        if block.userid == user_id or block.commitment == mod_exp(g, fingerprint_hash, p):
            return jsonify({"message": "User already registered"}), 400

    user_db[user_id] = fingerprint_hash
    C = mod_exp(g, fingerprint_hash, p)

    new_block = blockchain.add_block(user_id, {"action": "register"}, C)
    # broadcast_block(peer_nodes, new_block)

    return jsonify({"message": "Registration successful", "block": new_block.__dict__}), 200

@app.route('/initiate_zkp', methods=['POST'])
def initiate_zkp():
    data = request.get_json()
    user_id = data['userId']

    if user_id not in user_db:
        return jsonify({"message": "User not registered"}), 404

    T = data['T']
    q = p - 1
    c = challenge_verifier(q)

    user_db[user_id + '_T'] = T

    return jsonify({"challenge": c}), 200

@app.route('/verify_zkp', methods=['POST'])
def verify_zkp():
    data = request.get_json()
    user_id = data['userId']
    s = data['s']
    c = data['challenge']
    node_id = request.host  # Use the node's address as an identifier

    if user_id not in user_db or user_id + '_T' not in user_db:
        return jsonify({"message": "User not registered or commitment not found"}), 404

    T = user_db[user_id + '_T']
    H_f = user_db[user_id]
    C = mod_exp(g, H_f, p)

    if verify_proof(s, T, C, c):
        token = issue_token(user_id, node_id)
        if user_id not in issued_tokens:
            issued_tokens[user_id] = []
        issued_tokens[user_id].append(token)

        return jsonify({"message": "Login successful", "token": token}), 200
    else:
        return jsonify({"message": "Login failed"}), 401

@app.route('/authenticate', methods=['POST'])
def authenticate():
    data = request.get_json()
    user_id = data['userId']
    tokens = data['tokens']

    valid_tokens = 0
    for token in tokens:
        decoded_token = verify_token(token)
        if decoded_token and decoded_token['user_id'] == user_id:
            valid_tokens += 1

    if valid_tokens > len(peer_nodes) // 2:
        return jsonify({"message": "Authentication successful"}), 200
    else:
        return jsonify({"message": "Authentication failed"}), 401

@app.route('/process_request', methods=['POST'])
def process_request():
    data = request.get_json()
    user_id = data['userId']
    tokens = data['tokens']

    # Verify if a majority of tokens are valid
    valid_tokens = 0
    for token in tokens:
        decoded_token = verify_token(token)
        if decoded_token and decoded_token['user_id'] == user_id:
            valid_tokens += 1

    if valid_tokens > len(peer_nodes) // 2:
        # Broadcast to other authority nodes that the request is valid
        for node in peer_nodes:
            broadcast_block(node, {"user_id": user_id, "action": "process"})
        return jsonify({"message": "Request processed successfully"}), 200
    else:
        return jsonify({"message": "Request denied"}), 401

@app.route('/add_node', methods=['POST'])
def add_node():
    node_address = request.get_json()['node_address']
    if node_address not in peer_nodes:
        peer_nodes.append(node_address)
        return jsonify({"message": "Node added successfully"}), 200
    return jsonify({"message": "Node already exists"}), 400

@app.route('/sync_blockchain', methods=['GET'])
def sync_blockchain():
    chain_data = [block.__dict__ for block in blockchain.chain]
    response = jsonify(chain_data)
    response.headers.add('Content-Type', 'application/json')
    return response, 200

@app.route('/receive_block', methods=['POST'])
def receive_block():
    block_data = request.get_json()
    new_block = Block(
        block_data['userid'],
        block_data['previous_hash'],
        block_data['transaction'],
        block_data['commitment'],
        block_data['timestamp']
    )

    if blockchain.is_valid_chain():
        blockchain.chain.append(new_block)
        return jsonify({"message": "Block added successfully"}), 200
    else:
        return jsonify({"message": "Invalid block"}), 400

if __name__ == '__main__':
    app.run(port=5000)
