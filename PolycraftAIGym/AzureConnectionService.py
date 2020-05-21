from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import os
import re
import PolycraftAIGym.config as CONFIG


class AzureConnectionService:

    def __init__(self, debug_log, container_name='log-container'):
        self.blob_service_client = self._read_secret_key()
        self.debug_log = debug_log
        self.container_name = container_name

    def _read_secret_key(self):
        """
        Private method to read the connection string for connecting to Azure Storage
        :return: An @link={azure.storage.blob.BlobServiceClient} object if the connection string is valid. None otherwise.
        """
        key = 'AZURE_STORAGE_KEY="'
        with open("../.secretkeys", "r") as f:
            line = f.readline()
            while line != '':
                if key in line:
                    connect_str = line[line.find(key) + len(key):-1]
                    try:
                        blob_service_client = BlobServiceClient.from_connection_string(connect_str)
                        return blob_service_client
                    except:
                        self.debug_log.message("AzureBlobConnectionError: Check Azure Storage Key!")
                        return None
                line = f.readline()

        return None

    def upload_pal_messenger_logs(self, palMessenger, container=None):
        self.upload_file(palMessenger.log_file, container)

    def upload_file(self, filepath, container=None):
        """
        Uploads file to the Azure Blob, using a secret key as defined in a separate file.
        Acquire the SecretKey from AzureStorage, if needed
        TODO: Confirm that this works on Windows
        :param filepath: PosixPath object containing a path to the file. use filepath.name to get the file name
        :param container: name of container to be uploaded to. If None, defaults to using self.container_name
        :return: True if a file was successfully uploaded to the Azure Blob. False otherwise.
        """
        if self.blob_service_client is not None:
            if container is not None:
                container_to_use = container
            else:
                container_to_use = self.container_name
            blob_name = f"{CONFIG.TOURNAMENT_ID}_{CONFIG.AGENT_ID}_{filepath.name}"
            blob_client = self.blob_service_client.get_blob_client(container=container_to_use, blob=blob_name)
            try:
                with open(filepath, 'rb') as data:
                    blob_client.upload_blob(data)
            except FileNotFoundError:
                self.debug_log.message(f"Error: File not found! {filepath}")
                return False
            return True
        else:
            self.debug_log.message("ERROR: blob service client is null. Upload incomplete.")
            return False
