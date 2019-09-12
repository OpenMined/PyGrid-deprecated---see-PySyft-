import binascii
import json
import os
import requests
from requests_toolbelt.multipart import encoder, decoder
import sys

import torch as th
import syft as sy
from syft.workers.base import BaseWorker

from grid import utils as gr_utils

MODEL_LIMIT_SIZE = (1024 ** 2) * 100  # 100MB


class GridClient(BaseWorker):
    """GridClient."""

    def __init__(self, addr: str, verbose: bool = True, hook=None, id="grid", **kwargs):
        hook = sy.hook if hook is None else hook
        super().__init__(hook=hook, id=id, verbose=verbose, **kwargs)
        print(
            "WARNING: Grid nodes publish datasets online and are for EXPERIMENTAL use only."
            "Deploy nodes at your own risk. Do not use OpenGrid with any data/models you wish to "
            "keep private.\n"
        )
        self.addr = addr
        self._verify_identity()
        # We use ISO encoding for some serialization/deserializations
        # due to non-ascii characters.
        self._encoding = "ISO-8859-1"

    def _verify_identity(self):
        r = requests.get(self.addr + "/identity/")
        if r.text != "OpenGrid":
            raise PermissionError("App is not an OpenGrid app.")

    def _send_msg(self, message: bin, location: BaseWorker) -> bin:
        raise NotImplementedError

    def _send_http_request(
        self,
        route,
        data,
        request,
        N: int = 10,
        unhexlify: bool = True,
        return_response_text: bool = True,
    ):
        """Helper function for sending http request to talk to app.

        Args:
            route: App route.
            data: Data to be sent in the request.
            request: Request type (GET, POST, PUT, ...).
            N: Number of tries in case of fail. Default is 10.
            unhexlify: A boolean indicating if we should try to run unhexlify on the response or not.
            return_response_text: If True return response.text, return raw response otherwise.
        Returns:
            If return_response_text is True return response.text, return raw response otherwise.
        """
        url = os.path.join(self.addr, "{}".format(route))
        r = request(url, data=data) if data else request(url)
        r.encoding = self._encoding
        response = r.text if return_response_text else r

        # Try to request the message `N` times.
        for _ in range(N):
            try:
                if unhexlify:
                    response = binascii.unhexlify(response[2:-1])
                return response
            except:
                if self.verbose:
                    print(response)
                response = None
                r = request(url, data=data) if data else request(url)
                response = r.text

        return response

    def _send_streaming_post(self, route, data=None):
        """ Used to send large models / datasets using stream channel.

            Args:
                route : Service endpoint
                data : tensors / models to be uploaded.
            Return:
                response : response from server
        """
        # Build URL path
        url = os.path.join(self.addr, "{}".format(route))

        # Send data
        session = requests.Session()
        form = encoder.MultipartEncoder(data)
        headers = {"Prefer": "respond-async", "Content-Type": form.content_type}
        resp = session.post(url, headers=headers, data=form)
        session.close()
        return resp.content

    def _send_post(self, route, data=None, **kwargs):
        return self._send_http_request(route, data, requests.post, **kwargs)

    def _send_get(self, route, data=None, **kwargs):
        return self._send_http_request(route, data, requests.get, **kwargs)

    def _recv_msg(self, message: bin, N: int = 10) -> bin:
        message = str(binascii.hexlify(message))
        return self._send_post("cmd", data={"message": message}, N=N)

    def destroy(self):
        grid_name = self.addr.split("//")[1].split(".")[0]
        gr_utils.execute_command(
            "heroku destroy " + grid_name + " --confirm " + grid_name
        )
        if self.verbose:
            print("Destroyed node: " + str(grid_name))

    @property
    def models(self, N: int = 1):
        return json.loads(self._send_get("models/", N=N))

    def delete_model(self, model_id):
        return json.loads(
            self._send_post(
                "delete_model/", data={"model_id": model_id}, unhexlify=False
            )
        )

    def get_model_copy(self, model_id: str):
        """Gets a copy of a model to run locally."""

        def _is_large_model(result):
            return "multipart/form-data" in result.headers["Content-Type"]

        # Check if we can get a copy of this model
        result = json.loads(
            self._send_get("is_model_copy_allowed/{}".format(model_id), unhexlify=False)
        )
        if not result["success"]:
            raise RuntimeError(result["error"])

        try:
            # If the model is a plan we can just call fetch
            return sy.hook.local_worker.fetch_plan(model_id, self, copy=True)
        except AttributeError:
            result = self._send_get(
                "get_model/{}".format(model_id),
                unhexlify=False,
                return_response_text=False,
            )
            if result:
                if _is_large_model(result):
                    # If model is large, receive it by a stream channel
                    multipart_data = decoder.MultipartDecoder.from_response(result)
                    model_bytes = b"".join(
                        [part.content for part in multipart_data.parts]
                    )
                    serialized_model = model_bytes.decode("utf-8").encode(
                        self._encoding
                    )
                else:
                    # If model is small, receive it by a standard json
                    result = json.loads(result.text)
                    serialized_model = result["serialized_model"].encode(self._encoding)

                model = sy.serde.deserialize(serialized_model)
                return model
            else:
                raise RuntimeError(
                    "There was a problem while getting the model, check the server logs for more information."
                )

    def serve_model(
        self,
        model,
        model_id: str = None,
        allow_get_model_copy: bool = False,
        allow_run_inference: bool = False,
    ):
        """Hosts the model and optionally serve it using a Rest API.

        Args:
            model: A jit model or Syft Plan.
            model_id: An integer or string representing the model id used to retrieve the model
                later on using the Rest API. If this is not provided and the model is a Plan
                we use model.id, if the model is a jit model we raise an exception.
            allow_get_model_copy: If other workers should be able to fetch a copy of this model to run it locally set this to True.
            allow_run_inference: If other workers should be able to run inference using this model through a Rest API interface set this True.

        Returns:
            A json object representing a Rest API response.

        Raises:
            ValueError: if model_id is not provided and model is a jit model (aka does not have an id attribute).
        """
        if model_id is None:
            if isinstance(model, sy.Plan):
                model_id = model.id
            else:
                raise ValueError("Model id argument is mandatory for jit models.")

        # If the model is a Plan we send the model
        # and host the plan version created after
        # the send operation
        if isinstance(model, sy.Plan):
            # We need to use the same id in the model
            # as in the POST request.
            model.id = model_id
            model.send(self)
            res_model = model.ptr_plans[self.id]
        else:
            res_model = model

        serialized_model = sy.serde.serialize(res_model).decode(self._encoding)

        if sys.getsizeof(serialized_model) >= MODEL_LIMIT_SIZE:
            return json.loads(
                self._send_streaming_post(
                    "serve-model/",
                    data={
                        "model": (
                            model_id,
                            serialized_model,
                            "application/octet-stream",
                        ),
                        "encoding": self._encoding,
                        "model_id": model_id,
                        "allow_get_model_copy": str(allow_get_model_copy),
                        "allow_run_inference": str(allow_run_inference),
                    },
                )
            )
        else:
            return json.loads(
                self._send_post(
                    "serve-model/",
                    data={
                        "model": serialized_model,
                        "encoding": self._encoding,
                        "model_id": model_id,
                        "allow_get_model_copy": allow_get_model_copy,
                        "allow_run_inference": allow_run_inference,
                    },
                    unhexlify=False,
                )
            )

    def run_inference(self, model_id, data, N: int = 1):
        serialized_data = sy.serde.serialize(data)
        return json.loads(
            self._send_get(
                "models/{}".format(model_id),
                data={
                    "data": serialized_data.decode(self._encoding),
                    "encoding": self._encoding,
                },
                N=N,
            )
        )
