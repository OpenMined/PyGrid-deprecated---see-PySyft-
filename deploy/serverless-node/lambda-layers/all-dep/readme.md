Build a zip file containing all dependencies of PyGrid Node, to deploy to an AWS Lambda Layer.
The root file should be called `Python`, and contains all the dependencies.
```shell script
mkdir python
pip install -r requirements.txt -t python
zip -r all-dep.zip python
```