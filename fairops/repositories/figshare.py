import hashlib
import json
import os
import re

import requests
from requests.exceptions import HTTPError
from tqdm import tqdm


class FigshareClient:
    """
    A client for interacting with the Figshare API to manage projects, articles, and file uploads/downloads.
    """
    def __init__(self, api_token: str):
        """
        Initialize the Figshare client with an API token.

        Args:
            api_token (str): The Figshare API token for authentication.
        """
        if api_token is None:
            raise Exception("figshare API token must be set")

        self.api_token = api_token
        self.base_url = "https://api.figshare.com/v2"
        self.headers = {"Authorization": f"token {self.api_token}"}
        self.chunk_size = 10485760  # 10MB

    def _issue_request(self, method: str, url: str, data: dict = None, binary: bool = False, stream: bool = None):
        """
        Make an authenticated request to the Figshare API.

        Args:
            method (str): HTTP method (GET, POST, PUT, etc.).
            url (str): API endpoint URL.
            data (dict, optional): Request payload data.
            binary (bool, optional): Set to True for binary file uploads.
            stream (bool, optional): Set to True for streaming responses.

        Returns:
            dict or requests.Response: JSON response data or raw response object if streamed.
        """
        if data is not None and not binary:
            data = json.dumps(data)
        response = requests.request(
            method,
            url,
            headers=self.headers,
            data=data,
            stream=stream
        )

        try:
            response.raise_for_status()
            if stream is not None and stream:
                return response
            try:
                data = json.loads(response.content)
            except ValueError:
                data = response.content
        except HTTPError as error:
            print('Caught an HTTPError: {}'.format(error.message))
            print('Body:\n', response.content)
            raise

        return data

    def download_files(self, article_id: int, output_path: str) -> str:
        """
        Download all files associated with an article.

        Args:
            article_id (int): The Figshare article ID.
            output_path (str): Local directory to save downloaded files.

        Returns:
            str: Path to the downloaded files.
        """
        output_path = os.path.join(output_path, str(article_id))
        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)

        files = []
        try:
            files = self._issue_request(
                "GET",
                f"{self.base_url}/account/articles/{article_id}/files"
            )
        except:  # noqa: E722
            try:
                files = self._issue_request(
                    "GET",
                    f"{self.base_url}/articles/{article_id}/files"
                )
            except:  # noqa: E722
                raise Exception("DOI not found or insufficent permissions")

        for file in files:
            file_download_url = file["download_url"]
            file_name = file["name"]
            full_path = os.path.join(output_path, file_name)

            file_data = self._issue_request(
                "GET",
                file_download_url,
                stream=True
            )

            total_size = int(file_data.headers.get("content-length", 0))

            with open(full_path, "wb") as f, tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=file_name
            ) as progress_bar:
                for chunk in file_data.iter_content(chunk_size=8192):
                    f.write(chunk)
                    progress_bar.update(len(chunk))

        return output_path

    def download_files_by_doi(self, doi: str, output_path: str) -> str:
        """
        Download files using a Figshare DOI.

        Args:
            doi (str): The DOI of the Figshare article.
            output_path (str): Local directory to save downloaded files.

        Returns:
            str: Path to the downloaded files, or None if the article is not found.
        """
        doi_article_pattern = r"figshare\.(\d+)"
        match = re.search(doi_article_pattern, doi)
        article_id = None
        if match:
            article_id = match.group(1)
        else:
            print("Article not found")
            return None

        return self.download_files(article_id, output_path)

    def create_project(self, title: str, description: str) -> int:
        """
        Create a new project on Figshare.

        Args:
            title (str): The title of the project.
            description (str): A description of the project.

        Returns:
            int: The newly created project ID.
        """
        url = f"{self.base_url}/account/projects"
        data = {"title": title, "description": description}
        project = self._issue_request(
            "POST",
            url,
            data=data
        )
        return project["entity_id"]

    def create_article_in_project(self, project_id: int, title: str) -> int:
        """
        Create a new article within a Figshare project.

        Args:
            project_id (int): The Figshare project ID.
            title (str): The title of the article.

        Returns:
            int: The newly created article ID.
        """
        url = f"{self.base_url}/account/projects/{project_id}/articles"
        data = {"title": title}

        response = self._issue_request("POST", url, data=data)
        return response["entity_id"]

    def _get_file_check_data(self, file_name: str):
        """
        Calculate the MD5 checksum and file size.

        Args:
            file_name (str): The file path.

        Returns:
            tuple: (MD5 hash, file size in bytes).
        """
        with open(file_name, 'rb') as fin:
            md5 = hashlib.md5()
            size = 0
            data = fin.read(self.chunk_size)
            while data:
                size += len(data)
                md5.update(data)
                data = fin.read(self.chunk_size)
            return md5.hexdigest(), size

    def _initiate_new_upload(self, article_id: int, file_name: str):
        """
        Initiate a new file upload.

        Args:
            article_id (int): The ID of the article where the file will be uploaded.
            file_name (str): The local file path.

        Returns:
            dict: File upload details.
        """
        endpoint = f'{self.base_url}/account/articles/{article_id}/files'

        md5, size = self._get_file_check_data(file_name)
        data = {
            'name': os.path.basename(file_name),
            'md5': md5,
            'size': size
        }

        result = self._issue_request('POST', endpoint, data=data)
        result = self._issue_request('GET', result['location'])

        return result

    def _complete_upload(self, article_id: int, file_id: int):
        """
        Complete an upload after all parts have been uploaded.

        Args:
            article_id (int): The article ID.
            file_id (int): The file ID.
        """
        self._issue_request(
            "POST",
            f'{self.base_url}/account/articles/{article_id}/files/{file_id}'
        )

    def upload_part(self, file_info: dict, stream, part: dict):
        """
        Upload a part of a file.

        Args:
            file_info (dict): File upload details.
            stream (file object): Opened file stream.
            part (dict): Part metadata including start and end offsets.
        """
        udata = file_info.copy()
        udata.update(part)
        url = f'{udata["upload_url"]}/{udata["partNo"]}'

        stream.seek(part['startOffset'])
        data = stream.read(part['endOffset'] - part['startOffset'] + 1)

        self._issue_request('PUT', url, data=data, binary=True)

    def _upload_parts(self, data_file: str, file_info: dict, parent_pbar):
        """
        Upload a file in chunks to Figshare.

        Args:
            data_file (str): Local file path.
            file_info (dict): File upload details.
            parent_pbar (tqdm): Parent progress bar.
        """
        result = self._issue_request('GET', file_info["upload_url"])
        file_size = os.path.getsize(data_file)
        cur_part = 0

        with open(data_file, 'rb') as fin, tqdm(
            total=file_size,
            desc="  ↳ Uploading parts for file",
            unit="B",
            leave=False
        ) as parts_pbar:
            for part in result['parts']:
                self.upload_part(file_info, fin, part)

                uploaded_bytes = cur_part * self.chunk_size
                part_size = min(self.chunk_size, file_size - uploaded_bytes)
                parts_pbar.update(part_size)
                cur_part += 1
            parent_pbar.update(1)

    def upload_files_to_project(self, project_id: int, title: str, file_paths: list):
        """
        Upload multiple files to a Figshare project.

        Args:
            project_id (int): The Figshare project ID.
            title (str): The article title.
            file_paths (list): List of file paths to upload.
        """
        article_id = self.create_article_in_project(project_id, title)

        with tqdm(
            total=len(file_paths),
            desc="Uploading files",
            unit="file"
        ) as files_pbar:
            for file_path in file_paths:
                file_info = self._initiate_new_upload(article_id, file_path)
                self._upload_parts(file_path, file_info, files_pbar)
                self._complete_upload(article_id, file_info['id'])
