# FAIRops
[![PyPi Build Status](https://github.com/acomphealth/fairops/actions/workflows/ci.yml/badge.svg)](https://pypi.org/project/fairops/)

# Ops for Biomedical AI/ML Demo
1. DataOps: https://github.com/acomphealth/dataops
2. MLOps: https://github.com/acomphealth/mlops

# CLI Usage
## Configure Environment File
Create .env in the working directory with your repository API token(s). These are only needed if uploading to the specific repository.

```
FIGSHARE_API_TOKEN=yourtoken
ZENODO_API_TOKEN=yourtoken
```

## Docker Image Preservation
Publish image to repository (Zenodo, etc):

```
fairops docker publish REPO TAG ARCHIVE_PATH
```