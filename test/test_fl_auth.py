import json
import pytest
import binascii
import websockets
import aiounittest
from uuid import UUID

import torch as th
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import syft as sy

from test import GATEWAY_WS_URL
##from flask import Flask, session

import requests

def test_auth_test_1():
    server_config = {
            "user_id": '123',
            "JWT_VERIFY_API": None
        }

    response = requests.post('http://localhost:5000/federated/authenticate', json=server_config).json()


    assert response["status"] == "success"
    assert response["worker_id"] != None

def test_auth_test_2():
    params = dict(
    user_id = '123',
    JWT_VERIFY_API = 'google.com'
)
    response = requests.post('http://localhost:5000/federated/authenticate', json=params).json()


    assert response["error"] == "Authentication is required, please pass an 'auth_token'."

def test_auth_test_3():
    params = dict(
    user_id = '123',
    auth_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VyX2lkIjoidGVzdHlGdWxsZXIifQ.HP7lKBQBtJ3WdgUNy-lUtmWKJMZuyGtfCz0xx77LK3QIlidrCUcsSI-i7mtzT7d2IM45-kt11j3REiQJzv6xzz2SVs3riKTrOQHxjwzYQyPzlBaFU3mo3GUJZHKz3lrloQWcBEbPkYh7JmmFy7fPTKnq2yp4NCamlqunDcz86dg9Z5gaj8rDCd7Z-UZeQVDHU-wDx5EBZvctwa_WSkeyhCtgbW38AdMecwt1f4RLK3JSm0NxqHFDLrwjh3Qos4AuUs8r96qY9RmEq6jMJ7Y8tUUrsvyCqufs22fCpe6rlJPRRuuTifJLp96LJwx_fhfe3CPUm97wPbTEQdzP9sotfLUXGXd68w56hngy0q_1u2p0bp8vTOdStqFXd1LuNuQChLdygt9tXigt4-wuY0gBCiqvbXSn6JDhHcOiTRIWcZNrexN-xr4D4NktfjPlYFOpTSIdoV-8WvjomAZPzCQbFaSYBTUeIyhlPqA9cuytL2n_-otexJVFB-HOSSATyXfnYmKQj2Jwsgo2TqZdKHH2aUjvukmTY5ldZvomcG2qrFYg7Dq2C1cjgXsN-4Oa3RvmW1aquK7Ziute0ACaGD71orb9GNvPDIuZ1ohPl7u8iAdD46cQIueUCthAWoeFQiGsj9IDkUBvZeJZ4TB7GHB4w7PpsAyouHKY-dhNE1bEtWQ',
    JWT_VERIFY_API = 'google.com',
    RSA = True
)
    response = requests.post('http://localhost:5000/federated/authenticate', json=params).json()


    assert response["error"] == "The 'auth_token' you sent is invalid. Signature verification failed"

def test_auth_test_4():
    params = dict(
    user_id = '123',
    auth_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1c2VyX2lkIjoidGVzdHlGdWxsZXIifQ.j_-mTbLad2X39JAg2PVyOXFobkxzfO7zloDNdzMK6TevFlpX3AqZfaSRcmmT0pBSBqCDe72KL8GAd6nSOZsAj63TEpOaqM3btRicZN8A-TYsZiUAzDggPzD1MS7PAu6uXK11JBuWkLaVUhQpW0YDNDE5Co1jdmnjysmn7o1hipDgWUFhCgkDta78KuafZyHxLYZ5GNYXWQ57YTbdieJzivsqlk_eUyBGTFznzcQVDar2dIzIenAPgG05DitEnNBUPM4Ca_-vSZUre4vaZ-dfwOtnQia-N7tQ_kG72DH6sBom4KYVPKgLnz8DGG3W6oxskofLFcAs1veainbwstx5gwYs6WjUZ52_-gDAkdphliL3yO0boW5D5JckM8cuVbG7OgVCySSc9wO0aRDGWFyVQDz4UHfd15Vyc2JKrYXE18z8xcMyEVNVqo3drGZpMMootgAczhasokp7B2SHIVWA-fTnN0PZaYAibCxrCaYTo-UAXXbSH8NrGa0fcJRjQUtCyL4vipTPouGNRzkMcIYJVNA679WCaP6q5Z1G80DmV7ZxuDsdpQifIRIZIxMVKW7x2jkGsKAMKYjrCCNm8lhHV_CLsLztq0o6XeVSr3-f_XTx-m3Dgpd8qgmFsDW3k5nnCR-2JTuYG57o_2F7cbQL2J3wp17-e8R8ki0Xmd2VGFA',
    JWT_VERIFY_API = 'google.com',
    RSA = True
)
    response = requests.post('http://localhost:5000/federated/authenticate', json=params).json()


    assert response["status"] == "success"
    assert response["worker_id"] != None
    print(response)


def test_auth_test_5():
    params = dict(
    user_id = '123',
    auth_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxMjN9.pimvvf9CsF0anFkM_AgKbhI6rJjE3hOAYIIkwZazWFc',
    JWT_VERIFY_API = 'google.com',
    RSA = False
)
    response = requests.post('http://localhost:5000/federated/authenticate', json=params).json()


    assert response["error"] == "The 'auth_token' you sent is invalid."


def test_auth_test_6():
    params = dict(
    user_id = '123',
    auth_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxMjN9.tFR6rGpRZhymR83NRxuuMAZM65r7pq_9cCoar3rrKxc',
    JWT_VERIFY_API = 'google.com',
    RSA = False
)
    response = requests.post('http://localhost:5000/federated/authenticate', json=params).json()


    assert response["status"] == "success"
    assert response["worker_id"] != None
    print(response)


def test_auth_test_7():
    params = dict(
    user_id = '123',
    auth_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoxMjN9.tFR6rGpRZhymR83NRxuuMAZM65r7pq_9cCoar3rrKxc',
    JWT_VERIFY_API = 'google.com',
    RSA = False,
    get_to_post = True
)
    response = requests.post('http://localhost:5000/federated/authenticate', json=params).json()


    assert response["error"] == "The 'auth_token' you sent did not pass 3rd party verificaiton."
    




    
