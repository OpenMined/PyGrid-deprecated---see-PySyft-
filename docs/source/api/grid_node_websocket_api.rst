Grid Node Websocket API
=======================

All SocketIO endpoints will be detailed in this document.

Models
-------

| **Event** : ``/models``
| **Description** : Generate a list of models saved on the worker.
| **Method** : ``GET``
| **Auth required** : NO (can be changed)

Status Code: 200 OK
^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "success" : True,
        "models" : [model_id1, model_id2, ...] 
    }


.. code:: json

    {
        "success" : False,
        "error" : error_message
    }

Check if Copy for Model is Allowed
--------------------------------

| **Event** : ``/is_model_copy_allowed/<model_id>``
| **Description** : Check if the specified model is available for download.
| **Method** : ``GET``
| **Auth required** : NO (can be changed)

Status Code: 200 OK
^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "success" : True
    }

.. code:: json

    {
        "success" : False,
        "error" : MODEL_NOT_FOUND_MSG/NOT_ALLOWED_TO_DOWNLOAD_MSG
    }

Get Model
-----------

| **Event** : ``/get_model/<model_id>``
| **Description** : Try to download the specified model.
| **Method** : ``GET``
| **Auth required** : NO (can be changed)

Status Code: 200 OK
^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "serialized_model" : model
    }

Status Code: 403 Forbidden
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "error" : NOT_ALLOWED_TO_DOWNLOAD_MSG
    }

Status Code: 404 Not Found
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "error" : MODEL_NOT_FOUND_MSG
    }

Serve Model
-----------

| **Event** : ``/serve_model``
| **Description** : Try to save the model in Grid 
| **Method** : ``POST``
| **Content-Type** : application/json
| **Auth required** : NO (can be changed)

Request Body
^^^^^^^^^^^^

.. code:: json

    {
        "encoding" : encoding,
        "model_id" : model_id,
        "allow_download" : True/False,

    }

Status Code: 200 OK
^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "success" : True,
        "message" : Model saved with id: <model id>
    }

Status Code: 409 Conflict
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "success" : False,
        "message" : error_message
    }

Get Available Tags
------------------

| **Event** : ``/dataset-tags``
| **Description** : Get the dataset tags stored in this node
| **Method** : ``GET``
| **Auth required** : NO (can be changed)

Status Code: 200 OK
^^^^^^^^^^^^^^^^^^^

.. code:: json

    [tag1, tag2, ...]

Search Encrypted Models
-----------------------

| **Event** : ``/search-encrypted-models``
| **Description** : Search for a specific encrypted model_id that is hosted on this node
| **Method** : ``POST``
| **Content-Type** : application/json
| **Auth required** : NO (can be changed)

Request Body:
^^^^^^^^^^^^^

.. code:: json

    {       
        "model_id" : <model_id>
    }

Status Code: 200 OK
^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "workers" : [worker1, worker2, ...],
        "crypto_provider" : [crypto_provider]
    }

Status Code: 400 Bad Request
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "error" : "Invalid payload format"
    }

Status Code: 404 Not Found
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "error" : "Model ID not found!" 
    }

Search for dataset tag
----------------------

| **Event** : ``/search``
| **Description** : Search for specific dataset tag stored in this node
| **Method** : ``POST``
| **Content-Type** : application/json
| **Auth required** : NO (can be changed)

Request Body
^^^^^^^^^^^^

.. code:: json

    {
        "query" : tag_dataset
    }

Status Code: 200 OK
^^^^^^^^^^^^^^^^^^^

.. code:: json

    {
        "content" : True/False
    }

Status Code: 400 Bad Request
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: json

    {}
