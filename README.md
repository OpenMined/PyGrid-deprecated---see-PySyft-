![foobar-logo](https://raw.githubusercontent.com/OpenMined/design-assets/master/logos/PyGrid/horizontal-primary-trans.png)

![Tests](https://github.com/OpenMined/GridNode/workflows/Run%20tests/badge.svg)
![License](https://img.shields.io/github/license/OpenMined/GridNode)
![OpenCollective](https://img.shields.io/opencollective/all/openmined)

# PyGrid

PyGrid is a peer-to-peer network of data owners and data scientists who can collectively train AI models using PySyft. It is part of the [PyGrid Platform](https://github.com/OpenMined/PyGrid/):
- **PyGrid**.  A server based application used to manage/monitor/control and route grid Nodes/Workers remotely.
- GridNode. A server based application used to store and manage data access in a secure and private way.
- GridWorkers. Clientd based app that uses different Syft based libraries to perform federated learning (ex: syft.js, KotlinSyft, SwiftSyft).


## Installation

Use the package manager pip to install PyGrid

```bash
git clone https://github.com/OpenMined/pyGrid
pip install .
```

## Usage

```bash
python -m grid <arguments>
```
You can pass the arguments or use environment variables to set the gateway configs.  

**Arguments**
```
  -h, --help            show this help message and exit
required  arguments:
  --port PORT, -p PORT  Port number of the socket.io server, e.g. --port=8777.
                        Default is os.environ.get('GRID_GATEWAY_PORT', None).

optional arguments:
  --host HOST           Grid node host, e.g. --host=0.0.0.0. Default is
                        os.environ.get('GRID_GATEWAY_HOST','0.0.0.0').
  --num_replicas NUM_REPLICAS
                        Number of replicas to provide fault tolerance to model
                        hosting. If None no replica is used (aka num_replicas
                        = 1). Default is os.environ.get('NUM_REPLICAS', None).
  --start_local_db      If this flag is used a SQLAlchemy DB URI is generated
                        to use a local db. If not provide via DATABASE_URL
                        environment variable

```

**Environment Variables**
- `GRID_GATEWAY_PORT` -  Port to run server on.
- `GRID_GATEWAY_HOST` - The grid gateway host
- `NUM_REPLICAS` - Number of replicas to provide fault tolerance to model hosting
- `DATABASE_URL` - The gateway database URL
- `SECRET_KEY` - The secret key

Example:

```bash
python -m grid --id=alice --port=5000
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Contributors

Please make sure to fill this section in with **all former and current** contributors to the project. [Documentation on how to do this is located here.](https://github.com/all-contributors/all-contributors)

## License
[Apache License 2.0](https://choosealicense.com/licenses/apache-2.0/)