
### Steps to build docker image for kubernetes environment

We need to bundle the dependencies of the packages into docker image
>Note: Reason for bundling dependencies because if the pod or instance created have external ip restriction for downloading package from pypi
https://pip.pypa.io/en/latest/user_guide/#fast-local-installs

* ##### Create repo folder and download psutil and request module wheel files 

        python -m pip install wheel
        python -m pip wheel --wheel-dir=wheels apminsight
                

* ##### To build or install the python package use the below command 

        pip install --no-index --find-links=/home/apm/wheels apminsight



* #### we need to build docker image for multiple platform

        docker buildx create --use
        docker buildx build --platform  linux/arm64,linux/amd64,linux/386 -t site24x7/apminsight-pythonagent:latest --push .

##Docker Image Intro:

Quick Reference
#### What is APM Insight PythonAgent?

APM Insight is an application performance monitoring tool by Site24x7, which helps users track and analyze critical business transactions, trace errors across various microservices, and understand the impact of external components on your application's performance https://www.site24x7.com/help/apm/python-agent.html

Maintained by: Site24x7
How to use this image

This image is for installing python agent in kubernetes init-container setup,
help link: https://www.site24x7.com/help/apm/python-agent/add-python-agent-in-kubernetes.html?src=cross-links&pg=help

Where to get help: https://www.site24x7.com/community


```Download agent zip and extract it to any directory
Go to agent/ directory and run below commands - 

Step 1 -
python3 -m pip install --upgrade pip
Step 2- 

pip3 install setuptools wheel

Step 3- 

pip3 install twine

python3 setup.py sdist bdist_wheel

twine check dist/*

python3 -m twine upload --repository pypi dist/*

--> It will ask Username and password 

API token must be created and used as password

uname should be used as __token__

```