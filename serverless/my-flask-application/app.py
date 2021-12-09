# app.py
import os
import boto3

from flask import Flask, jsonify, request

app = Flask(__name__)


USERS_TABLE = os.environ['USERS_TABLE']
client = boto3.client('dynamodb')

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/getuser/<string:user_id>/<string:id>")
def get_user(user_id, id):
    resp = client.get_item(
        TableName=USERS_TABLE,
        Key={
            'userId': { 'S': user_id },
            'currDatePlusUserId': {'S': id}
        }
    )
    item = resp.get('Item')
    if not item:
        return jsonify({'error': 'User does not exist'}), 404

    return jsonify({
        'userId': item.get('userId').get('S'),
        'name': item.get('name').get('S')
    })

import datetime

# using GET to simplify sending vlaues
@app.route("/createuser/<string:user_id>/<string:name>", methods=["GET"])
def create_user(user_id, name):
    #user_id = request.json.get('userId')
    #name = request.json.get('name')
    now = datetime.datetime.now()
    currDatePlusUserId = f"{now.strftime('%m%d%y')}-{user_id}"
    if not user_id or not name:
        return jsonify({'error': 'Please provide userId and name'}), 400

    resp = client.put_item(
        TableName=USERS_TABLE,
        Item={
            'userId': {'S': user_id },
            'currDatePlusUserId': {'S': currDatePlusUserId },
            'name': {'S': name}
        }
    )

    return jsonify({
        'userId': user_id,
        'currDatePlusUserId': currDatePlusUserId,
        'name': name
    })