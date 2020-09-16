Build a zip file containing all dependencies of PyGrid Node, to deploy to an AWS Lambda Layer.
The root file should be called `Python`, and contains all the dependencies.
```shell script
mkdir python
pip install -r requirements.txt -t python
```
Let us remove the unnecessary files now, and create a zip file to upload to lambda layer.
```shell script
cd python
rm -r *.whl *.dist-info __pycache__    # Remove unnecessary files
cd ..
zip -r all-dep.zip python
```