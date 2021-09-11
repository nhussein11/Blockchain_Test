#Creando una blockchain 

import datetime
import hashlib
import json #Para codificar los bloques antes de hashearlos
from flask import Flask,jsonify, request 

import requests
from uuid import uuid4
from urllib.parse import urlparse


# 1- Armando la cadena de bloques como tal
class Blockchain:
    def __init__(self):
        self.chain=[]
        self.transactions=[]
        self.create_block(proof=1, previous_hash='0') #Creacion del bloque genesis
        #consenso:
        self.nodes = set()
        
    def add_node(self, address):
        parsed_url=urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    def replace_chain(self):
        network=self.nodes
        longest_chain= None
        max_lenght = len(self.chain)
        #Para ir a traves de todos los nodos en la red
        for node in network:
            response=requests.get(f'https//{node}/get_chain')
            if response.status_code==200:
                lenght= response.json(['lenght'])
                chain=response.json(['chain'])
                if lenght > max_lenght and self.is_chain_valid(chain):
                    max_lenght=lenght
                    longest_chain=chain
                    
            if longest_chain:
                self.chain=longest_chain
                return True
            return False


    
    
    def create_block(self,proof,previous_hash):
        #creo el diccionario
        block={
            'index': len(self.chain)+1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash':previous_hash,
            'transactions': self.transactions
        }
        #Vacio la lista para evitar duplicados
        self.transactions=[]
        self.chain.append(block)
        return block
    
    def add_transaction(self,sender, receiver, amount):
        self.transactions.append({'sender': sender, 
                                  'receiver': receiver, 
                                  'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index']+1

    def get_previous_block(self):
        return self.chain[-1] #Con -1 obtenemos el ultimo bloque de la cached_name

    def proof_of_work(self,previous_proof): #Nro o pedazo de dato que los minero buscan encontrar para justamente minar o agregar un bloque a la cadena
        new_proof=1 
        check_proof= False
        
        while check_proof is False:
            #Se define la operacion, en este caso como es un ejemplo sencillo es: el cuadrado del new_proof menos el cuadrado del previous_proof
            #Luego se codifica todo en sha256
            hash_operation=hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            #Nivel de dificultad -> si los primeros 4 caracteres (en este caso 4 porque es un ejemplo, en las monedas actuales es 20 o más)
            if hash_operation[:4]=='0000':
                check_proof=True
            else:
                new_proof+=1
            return new_proof
    def hash(self, block):
        encode_block = json.dumps(block, sort_keys=True).encode() #dic del bloque ordenado por las llaves y se codifica en sha256
        return hashlib.sha256(encode_block).hexdigest()
    def is_chain_valid (self, chain):
        previous_block = chain[0] 
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof'] #proof anterior
            proof = block['proof'] #proof actual
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4]!= '0000':
                return False
            
            previous_block = block
            block_index += 1 
        return True

# 2- Minando la blockchain 
#Flash quickstart
app=Flask(__name__) 


#Direccion para el nodod en puerto 5000
node_address=str(uuid4()).replace('-','')

blockchain = Blockchain()
#Minando un nuevo bloque
@app.route('/mine_block', methods=['GET'])

def mine_block ():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    #Mando 1 por ej
    blockchain.add_transaction(sender=node_address, receiver='3er participe ', amount='1')
    block = blockchain.create_block(proof, previous_hash)

    response = {'message': 'Felicidades, haz minado un bloque!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof':block['proof'],
                'previous_hash':block['previous_hash'],
                'transactions':block['transactions']
                }
    return jsonify(response), 200 #Usando el codigo http code 200, como ejemplo, se puede usar otro la


#Obteniendo cadena completa
@app.route('/get_chain', methods=['GET'])

def get_chain():
    response={  'chain': blockchain.chain,
                'length': len(blockchain.chain)
            }   
    return jsonify(response), 200

#Evaluando la validez de la cadena de bloques
@app.route('/is_valid', methods=['GET'])

def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message' : 'Todo bien, el Blockchain es valido' }
    else:
        response = {'message' : 'Error, el Blockchain NO es valido' }
    return jsonify(response), 200

    
#Agregar nueva transaccion
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Algun elemento de la transaccion esta faltando', 400 #http de error
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'])
    response = {'message': f'La transaccion sera añadida al bloque {index}'}
    return jsonify(response), 201

    
    
#3 - Descentralizacion Blockchain

#Conexion de nuevos nodos
@app.route('/connect_node', methods=['POST'])
def  connect_node():
    json=request.get_json()
    nodes=json.get('nodes')
    if nodes is None: 
        return "No Node", 401 #Como estoy con el metodo post el codigo http es 401 y no 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'Todos los nodos estan conectados. El NicoCoin blockchain contiene los siguientes nodos:',
                'total_nodes': list(blockchain.nodes)
                }
    return jsonify(response), 201
 
#Reemplazar la cadena por la mas larga
@app.route('/replace_chain', methods=['GET'])

def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced :
        response = {'message' : 'Los nodos tenian diferentes cadenas... la cadena fue reemplazada por la mas larga',
                    'new_chain': blockchain.chain
                    }
    else:
        response = {'message' : 'Todo bien... la cadena es la mas larga',
                    'actual_chain':  blockchain.chain
                    }
    return jsonify(response), 200   
    
    
   
#Corriendo app
if __name__ == '__main__':
    app.run( host='0.0.0.0', port='5003') 