Build a zip file containing all dependencies of PyGrid Node, to deploy to an AWS Lambda Layer.
The root file should be called `Python`, and contains all the dependencies.
```shell script
mkdir python
pip install -r requirements.txt -t python
```
AWS Lambda uses Amazon linux operating system. So we will replace our installed Numpy with a Numpy which is compatible with Amazon Linux OS.
```shell script
cd python
rm -r numpy
wget https://files.pythonhosted.org/packages/f5/bf/4981bcbee43934f0adb8f764a1e70ab0ee5a448f6505bd04a87a2fda2a8b/numpy-1.16.1-cp36-cp36m-manylinux1_x86_64.whl
unzip numpy-1.16.1-cp36-cp36m-manylinux1_x86_64.whl
```
Let us remove the unnecessary files now, and create a zip file to upload to lambda layer.
```shell script
rm -r *.whl *.dist-info __pycache__    # Remove unnecessary files
cd ..
zip -r all-dep.zip python
```