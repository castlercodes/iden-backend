import hashlib
import json
import time

class Block:
    def __init__(self, user_id, previous_hash, transaction, commitment, timestamp=None):
        self.userid = user_id
        self.previous_hash = previous_hash
        self.transaction = transaction
        self.timestamp = timestamp or time.time()
        self.commitment = commitment
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            'user_id': self.userid,
            'previous_hash': self.previous_hash,
            'transaction': self.transaction,
            'timestamp': self.timestamp,
            'commitment': self.commitment,
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        return Block("first node", "0", "Genesis Block", "genesis_commitment")

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, user_id, transaction, commitment):
        last_block = self.get_last_block()
        new_block = Block(user_id, last_block.hash, transaction, commitment)
        self.chain.append(new_block)
        return new_block

    def is_valid_chain(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block.previous_hash != previous_block.hash:
                return False
            if current_block.hash != current_block.calculate_hash():
                return False
        return True
