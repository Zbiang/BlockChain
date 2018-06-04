import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request


class BlockChain:

    def __init__(self):
        self.chain = []
        self.current_transcations = []
        self.nodes = set()

        self.new_block(proof=100, previous_hash=1)

    def register_node(self, address: str):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def resolve_conflicts(self):
        neighbours = self.nodes
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.current_transcations) + 1,
            'timestamp': time(),
            'transcations': self.current_transcations,
            'proof': proof,
            'previous': previous_hash or self.hash(self.last_block)
        }

        self.current_transcations = []
        self.chain.append(block)
        return block

    def new_transcations(self, sender, recipient, amount) -> int:
        self.current_transcations.append(
            {
                'sender': sender,
                'recipient': recipient,
                'amount': amount
            }
        )
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof: int) -> int:
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    def valid_proof(self, last_proof: int, proof: int) -> bool:
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[0:4] == '0000'

app = Flask(__name__)
block_chain = BlockChain()
node_identifier = str(uuid4()).replace('-', '')


@app.route("/transcations/new", methods=["POST"])
def new_transcation():
    values = request.get_json()
    required = ["sender", "recipient", "amount"]

    if values is None:
        return "Missing values", 400

    if not all(k in values for k in required):
        return "Missing values", 400
    index = block_chain.new_transcations(values["sender"],
                                 values["recipient"],
                                 values["amount"])
    response = {"message": f'Transaction will be added to Block {index}'}
    return jsonify(response), 201

@app.route("/mine", methods=["GET"])
def mine():
    last_block = block_chain.last_block
    last_proof = last_block['proof']
    proof = block_chain.proof_of_work(last_proof)

    block_chain.new_transcations(sender=0,
                                 recipient=node_identifier,
                                 amount=1)
    block = block_chain.new_block(proof, None)
    response = {
        'message': 'New Block Forged',
        'index': block['index'],
        'transcations': block['transcations'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }

    return jsonify(response), 200

@app.route("/chain", methods=["GET"])
def full_chain():
    response = {
        'chain': block_chain.chain,
        'length': len(block_chain.chain)
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=["POST"])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: please supply a valid list of nodes", 400
    for node in nodes:
        block_chain.register_node(node)
    response = {
        'message': "New nodes have been added",
        'total_nodes': list(block_chain.nodes)
    }

    return jsonify(response), 201

if __name__ == "_main__":
    app.run(host="0.0.0.0", port=5000)



