# PyGrid imports
from ..codes import MSG_FIELD, RESPONSE_MSG, CYCLE, FL_EVENTS
from ..processes import process_manager

# Generic imports
import jwt
import uuid
import json
import base64
import requests


def verify_token(auth_token, model_name, model_version="latest"):

    server_config, _ = process_manager.get_configs(
        name=model_name, version=model_version
    )
    auth_config = server_config.get("authentication", None)

    HIGH_SECURITY_RISK_NO_AUTH_FLOW = True if auth_config is None else False

    if not HIGH_SECURITY_RISK_NO_AUTH_FLOW:
        """stub DB vars"""
        JWT_VERIFY_API = auth_config.get("endpoint", None)

        pub_key = auth_config.get("pub_key", None)
        SECRET = auth_config.get("secret", None)
        """end stub DB vars"""

        if auth_token is None:
            return {
                "error": "Authentication is required, please pass an 'auth_token'.",
                "status": RESPONSE_MSG.ERROR,
            }
        else:
            base64Header, base64Payload, signature = auth_token.split(".")
            header_str = base64.b64decode(base64Header)
            header = json.loads(header_str)
            _algorithm = header["alg"]

            try:
                if secret is not None:
                    payload_str = base64.b64decode(base64Payload)
                    payload = json.loads(payload_str)
                    jwt.decode(payload, SECRET)

                if pub_key is not None:
                    jwt.decode(auth_token, pub_key, _algorithm)

            except Exception as e:
                if e.__class__.__name__ == "InvalidSignatureError":
                    return {
                        "error": "The 'auth_token' you sent is invalid. " + str(e),
                        "status": RESPONSE_MSG.ERROR,
                    }

            if JWT_VERIFY_API is not None:
                external_api_verify_data = {"auth_token": f"{auth_token}"}
                verification_result = requests.post(
                    JWT_VERIFY_API, data=json.dumps(external_api_verify_data)
                )

                if verification_result.status_code != 200:
                    return {
                        "error": "The 'auth_token' you sent did not pass 3rd party verificaiton. ",
                        "status": RESPONSE_MSG.ERROR,
                    }

            return {
                "auth_token": f"{auth_token}",
                "status": RESPONSE_MSG.SUCCESS,
            }
    else:
        return {"status": RESPONSE_MSG.SUCCESS}
