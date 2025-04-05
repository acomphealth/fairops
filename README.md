# FAIRops
[![PyPi Build Status](https://github.com/acomphealth/fairops/actions/workflows/ci.yml/badge.svg)](https://pypi.org/project/fairops/)

[![CodeCov Status](https://codecov.io/gh/acomphealth/fairops/graph/badge.svg)](https://codecov.io/gh/acomphealth/fairops)

[![ReadTheDocs](https://readthedocs.org/projects/fairops/badge/?version=latest)](https://fairops.readthedocs.io/en/latest/?badge=latest)

# Installation
To install the fairops library:
```
pip install fairops
```

For developers of the fairops library:
```
conda env create -f environment_dev.yml
conda activate fairopsdev
```

# Programmatic Usage
Documentation for programmatic usage of the fairops library can be found at: https://fairops.readthedocs.io/en/latest

# CLI Usage
## Configure Environment Variables
The python-dotenv library is used for configuration management via environment variables (only needed if using methods that depend on the variable, such as Zenodo/Figshare). The environment variables can be set manually or within a configuration file. The order or priority is:

1. .env file within the current working directory
2. .env file located in /USERHOME/.config/fairops
3. Existing environment variables

If a .env configuration file is present, use of the fairops CLI will overwrite the existing environment variables. The .env files can be generated manually or via the CLI. For details on which modules need to be/can be configured, run:
```
fairops configure
```

The .env file can also be generated manually with the following variables:
```
FIGSHARE_API_TOKEN=yourtoken
ZENODO_API_TOKEN=yourtoken
```

To determine which variables are currently being used by the CLI, run:
```
fairops configure which
```

## Docker Image Preservation
To generate an archive/artifact for a Docker image and publish it to a repository, run the following command (requires Docker to be running locally):
```
fairops docker publish IMAGEREPO IMAGETAG
```

# Demo Applications
Two demo applications have been developed to showcase implementation and integration of the fairops library:

1. DataOps Demo: https://github.com/acomphealth/dataops
2. MLOps Demo: https://github.com/acomphealth/mlops
