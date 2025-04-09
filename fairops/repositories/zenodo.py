import json
import os
from urllib.parse import urlencode
from fairops.utils.decorators import private

import requests
from tqdm import tqdm


@private
class FileWithProgress:
    def __init__(self, file_path, desc=None):
        self.file = open(file_path, "rb")
        self.total = os.path.getsize(file_path)
        self.pbar = tqdm(total=self.total, unit="B", unit_scale=True, desc=desc or os.path.basename(file_path))

    def __len__(self):
        return self.total  # This helps requests verify size when Content-Length is set

    def read(self, size=-1):
        chunk = self.file.read(size)
        self.pbar.update(len(chunk))
        return chunk

    def close(self):
        self.file.close()
        self.pbar.close()


# TODO: Add documentation and variable typing
# TODO: Implement ABC
class ZenodoClient:
    """
    A client for interacting with the Zenodo API to manage projects, articles, and file uploads/downloads.
    """
    def __init__(self, api_token: str):
        """
        Initialize the Zenodo client with an API token.

        Args:
            api_token (str): The Zenodo API token for authentication.
        """
        if api_token is None:
            raise Exception("Zenodo API token must be set.")

        self.api_token = api_token
        self.base_url = "https://zenodo.org/api/"
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

    def create_project(self, title: str, description: str):
        """Create a draft record in Zenodo."""
        url = f'{self.base_url}deposit/depositions'
        data = {
            "metadata": {
                "title": title,
                "description": description,
                "upload_type": "dataset"
            }
        }
        response = requests.post(url, headers=self.headers, data=json.dumps(data))
        response_json = response.json()
        if response.status_code == 201:
            return response_json['id']
        else:
            print(f"Error creating draft: {response.text}")
            return None

    @private
    def _get_upload_url(self, deposition_id):
        """Get the upload URL for a specific deposition using the deposition ID."""
        url = f'{self.base_url}deposit/depositions/{deposition_id}'
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            upload_url = response.json()['links']['bucket']
            return upload_url
        else:
            print(f"Error fetching upload URL: {response.text}")
            return None

    # TODO: Add doc reference that project_id == deposition_id for Zenodo
    def upload_files_to_project(self, project_id, file_paths, title=None):
        """Upload a large file to Zenodo draft using PUT (streaming upload)."""
        success = True
        for file_path in tqdm(file_paths, desc="Uploading files", unit="file"):
            upload_url = self._get_upload_url(project_id)
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)

            # Prepare the headers
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/octet-stream',
                'Content-Length': str(file_size),
                'Content-Disposition': f'attachment; filename="{file_name}"'
            }

            file_obj = FileWithProgress(file_path)

            # Open the file and stream it to Zenodo
            response = requests.put(
                f"{upload_url}/{file_name}",
                headers=headers,
                data=file_obj
            )

            if response.status_code != 201:
                success = False
        
        if success:
            result = {
                "url": f"https://zenodo.org/uploads/{project_id}",
                "article_id": None,
                "project_id": project_id
            }
            return result
        else:
            print(f"Error uploading file: https://zenodo.org/uploads/{project_id}")
            return None

    def download_files_by_id(self, record_id, download_path):
        """Download a file from Zenodo."""
        url = f'{self.base_url}records/{record_id}'
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            record = response.json()
            file_url = None

            # Find the file URL in the response
            for file in record['files']:
                file_url = file['links']['download']

                if file_url:
                    file_data = requests.get(file_url)

                    if file_data.status_code == 200:
                        with open(download_path, 'wb') as f:
                            f.write(file_data.content)
                        print(f"File downloaded to {download_path}")
                        return True
                    else:
                        print(f"Error downloading file: {file_data.text}")
                        return False
            else:
                print("File ID not found in record.")
                return False
        else:
            print(f"Error fetching record: {response.text}")
            return False

    # Adapted from: https://github.com/space-physics/pyzenodo3/blob/main/src/pyzenodo3/base.py
    # https://doi.org/10.5281/zenodo.3537730
    @private
    def _find_record_by_doi(self, doi: str):
        params = {"q": f"conceptdoi:{doi.replace('/', '\\/')}"}
        url = self.base_url + "records?" + urlencode(params)
        response = requests.get(url, headers=self.headers).json()
        hits = response["hits"]["hits"]

        if len(hits) > 0:
            return hits[0]
        else:
            params = {"q": f"doi:{doi.replace('/', '\\/')}"}
            url = self.base_url + "records?" + urlencode(params)
            response = requests.get(url, headers=self.headers).json()
            hits = response["hits"]["hits"]

            if len(hits) > 0:
                return hits[0]

        return None

    def download_files_by_doi(self, doi, download_dir):
        """Download all files from a Zenodo record given its DOI."""
        # Get the record details using the DOI
        record = self._find_record_by_doi(doi)

        if record is not None:
            # Ensure download directory exists
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)

            # Loop through each file in the record and download it
            for file in record['files']:
                file_url = file['links']['self']
                file_name = file['key']
                base_path = os.path.dirname(file_name)
                file_dir = os.path.join(download_dir, base_path)
                if not os.path.exists(file_dir):
                    os.makedirs(file_dir)
                download_path = os.path.join(download_dir, file_name)

                file_data = requests.get(file_url)

                if file_data.status_code == 200:
                    with open(download_path, 'wb') as f:
                        f.write(file_data.content)
                    print(f"Downloaded {file_name} to {download_path}")
                else:
                    print(f"Error downloading file: {file_data.text}")

            return True
        else:
            print(f"Error fetching record: {doi}")
            return False
