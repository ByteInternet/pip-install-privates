# pip-install-privates
Install pip packages from private repositories without an ssh agent


# Usage
To use pip-install-privates, you need a Personal Access Token from Github. Go to [**Settings** > **Personal access tokens**](https://github.com/settings/tokens) and click *Generate new token*. Make sure to give the **repo** permission (*Full control of private repositories*). Copy the generated token and store it somewhere safe. Then use it in the command below.

```
pip install git+https://github.com/ByteInternet/pip-install-privates.git@0.2#egg=pip-install-privates
pip-install-privates --token <my-token> requirements.txt
```

## --help
```
usage: install.py [-h] [--token TOKEN] req_file

Install all requirements from specified file with pip. Optionally transform
editable URL's to private repo's to use a given Personal Access Token for
github. That way installing them does not depend on a ssh-agent with suitable
keys. Which you don't have when installing requirements in a Docker.
These URLs will also be stripped of the -e flag, so they're installed globally.

This means that the following URL:
  -e git+git@github.com:MyOrg/my-project.git@my-tag#egg=my_project
would be transformed to:
  git+https://<token>:x-oauth-basic@github.com/MyOrg/my-project.git@my-tag#egg=my_project

Non-private GitHub URL's (git+https) and non-GitHub URL's are kept as-is, but
are also stripped of the -e flag. If no token is given, private URLs will be
kept, including the -e flag (otherwise they can't be installed at all).

positional arguments:
  req_file              path to the requirements file to install

optional arguments:
  -h, --help            show this help message and exit
  --token TOKEN, -t TOKEN
                        Your Personal Access Token for private GitHub
                        repositories
```

# Hacking & testing
Everything should run smoothly on python 2.7, 3.4, 3.5 and 3.6

```
mkvirtualenv -a $PWD pip-install-privates
pip install -U pip
pip install -r requirements.txt
```

```
nosetests
tox
```
