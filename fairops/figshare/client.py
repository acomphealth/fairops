import requests
import os
import hashlib
import json
from tqdm import tqdm
from requests.exceptions import HTTPError
import re


class FigshareClient:
    def __init__(self, api_token: str):
        """Initialize the Figshare client with an API token."""
        self.api_token = api_token
        self.base_url = "https://api.figshare.com/v2"
        self.headers = {"Authorization": f"token {self.api_token}"}
        self.chunk_size = 10485760  # 10MB

    def issue_request(self, method, url, data=None, binary=False, stream=None):
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

    # def get_all_articles(self):
    #     articles = self.issue_request(
    #         "GET",
    #         f"{self.base_url}/account/articles"
    #     )
    #     if articles is None:
    #         return []
    #     return articles

    def download_files(self, article_id, output_path):
        output_path = os.path.join(output_path, str(article_id))
        if not os.path.exists(output_path):
            os.makedirs(output_path, exist_ok=True)

        files = self.issue_request(
            "GET",
            f"{self.base_url}/account/articles/{article_id}/files"
        )

        for file in files:
            file_download_url = file["download_url"]
            file_name = file["name"]
            full_path = os.path.join(output_path, file_name)

            file_data = self.issue_request(
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

    def download_files_by_doi(self, doi, output_path):
        doi_article_pattern = r"figshare\.(\d+)"
        match = re.search(doi_article_pattern, doi)
        article_id = None
        if match:
            article_id = match.group(1)
        else:
            print("Article not found")
            return None

        return self.download_files(article_id, output_path)

    def create_project(self, title: str, description: str):
        """Create a new project on Figshare."""
        url = f"{self.base_url}/account/projects"
        data = {"title": title, "description": description}
        project = self.issue_request(
            "POST",
            url,
            data=data
        )
        return project["entity_id"]

    def create_article_in_project(self, project_id: int, title: str):
        """Create an article within a project."""
        url = f"{self.base_url}/account/projects/{project_id}/articles"
        data = {"title": title}

        response = self.issue_request("POST", url, data=data)
        return response["entity_id"]

    def get_file_check_data(self, file_name):
        with open(file_name, 'rb') as fin:
            md5 = hashlib.md5()
            size = 0
            data = fin.read(self.chunk_size)
            while data:
                size += len(data)
                md5.update(data)
                data = fin.read(self.chunk_size)
            return md5.hexdigest(), size

    def initiate_new_upload(self, article_id, file_name):
        endpoint = f'{self.base_url}/account/articles/{article_id}/files'

        md5, size = self.get_file_check_data(file_name)
        data = {
            'name': os.path.basename(file_name),
            'md5': md5,
            'size': size
        }

        result = self.issue_request('POST', endpoint, data=data)
        result = self.issue_request('GET', result['location'])

        return result

    def complete_upload(self, article_id, file_id):
        self.issue_request(
            "POST",
            f'{self.base_url}/account/articles/{article_id}/files/{file_id}'
        )

    def upload_part(self, file_info, stream, part):
        udata = file_info.copy()
        udata.update(part)
        url = f'{udata["upload_url"]}/{udata["partNo"]}'

        stream.seek(part['startOffset'])
        data = stream.read(part['endOffset'] - part['startOffset'] + 1)

        self.issue_request('PUT', url, data=data, binary=True)

    def upload_parts(self, data_file, file_info, parent_pbar):
        result = self.issue_request('GET', file_info["upload_url"])
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

    def upload_files_to_project(self, project_id, title, file_paths):
        article_id = self.create_article_in_project(project_id, title)

        with tqdm(
            total=len(file_paths),
            desc="Uploading files",
            unit="file"
        ) as files_pbar:
            for file_path in file_paths:
                file_info = self.initiate_new_upload(article_id, file_path)
                self.upload_parts(file_path, file_info, files_pbar)
                self.complete_upload(article_id, file_info['id'])
