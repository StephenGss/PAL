from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity
from os import path
import re
import pyodbc
import config as CONFIG
from collections import OrderedDict
import distutils, distutils.util
from PalMessenger import PalMessenger
from azure.core.exceptions import ServiceRequestError, ServiceRequestTimeoutError, ServiceResponseError
import configparser


class AzureConnectionService:

    def __init__(self, debug_log, container_name='log-container'):
        self.configs = self._check_for_configs()
        self.debug_log = debug_log
        self.container_name = container_name

        self.blob_service_client = self._read_secret_key()
        self.sql_connection = self._get_sql_connection()
        self.cursor = self.sql_connection.cursor()

    def _check_for_configs(self):
        if path.exists("../secret.ini"):
            configs = configparser.ConfigParser()
            configs.read("../secret.ini")
            return configs
        else:
            return None

    def is_connected(self):
        if self.blob_service_client is not None and self.sql_connection is not None:
            return True
        return False

    def _get_sql_connection(self):
        if self.configs is None:
            return None
        Driver = "{ODBC Driver 17 for SQL Server}"
        Server="tcp:polycraft.database.windows.net,1433"
        Database = "tournament_database"
        Uid = self.configs['azure']['SQL_USERNAME']
        Pwd = self.configs['azure']['SQL_PASSWORD']
        Encrypt = "yes"
        TrustServerCertificate = "yes"
        ConnectionTimeout = 30
        cxn = f'Driver={Driver};Server={Server};Database={Database};Uid={Uid};Pwd={Pwd};Encrypt={Encrypt};TrustServerCertificate={TrustServerCertificate};Connection Timeout={ConnectionTimeout};'
        try:
            db = pyodbc.connect(cxn)
            return db
        except:
            self.debug_log.message("Error in SQL Connection")
            return None

    def _read_secret_key(self):
        """
        Private method to read the connection string for connecting to Azure Storage
        :return: An @link={azure.storage.blob.BlobServiceClient} object if the connection string is valid. None otherwise.
        """
        if self.configs is None:
            self.debug_log.message("AzureBlobConnectionError: Check Azure Storage Key!")
            return None

        return BlobServiceClient.from_connection_string(self.configs['azure']['AZURE_STORAGE_KEY'])
        # table_service = TableService(connection_string=connect_str)

    def send_score_to_azure(self, score_dict, game_id):
            if self.configs is None:
                self.debug_log.message("No Config File available for SQL Connection")
                return None

            vals = OrderedDict()
            vals['Task_Name'] = CONFIG.GAMES[game_id]
            vals['Agent_Name'] = str(CONFIG.AGENT_ID)
            vals['TournamentNm'] = str(CONFIG.TOURNAMENT_ID)
            vals['Game'] = int(game_id)
            vals['TournamentDate'] = PalMessenger.time_now_str()
            vals['NoveltyFlag'] = int(score_dict[game_id]['novelty'])
            vals['GroundTruth'] = int(score_dict[game_id]['groundTruth'])
            vals['NoveltyDetected'] = int(score_dict[game_id]['noveltyDetect'])
            vals['NoveltyDetectStep'] = int(score_dict[game_id]['noveltyDetectStep'])
            vals['NoveltyDetectTime'] = score_dict[game_id]['noveltyDetectTime']
            vals['Reward'] = float(score_dict[game_id]['adjustedReward'])
            vals['Total_Step_Cost'] = float(score_dict[game_id]['totalCost'])
            vals['Total_Steps'] = float(score_dict[game_id]['step'])
            vals['Total_Time'] = float(score_dict[game_id]['elapsed_time'])
            vals['StartTime'] = score_dict[game_id]['startTime']
            vals['EndTime'] = score_dict[game_id]['endTime']
            vals['Complete'] = distutils.util.strtobool(score_dict[game_id]['success'])
            vals['Reason'] = score_dict[game_id]['success_detail']
            vals['LogBlob'] = ""
            vals['AgentBlob'] = ""
            vals['DebugBlob'] = ""

            dictionary_as_tuple_list = [tuple(vals.values())]
            self.debug_log.message(f"Sending Score to SQL: {dictionary_as_tuple_list}")
            try:
                self.cursor.executemany(f"""
                    INSERT INTO RESULTS_TEST (Task_Name,Agent_Name,Tournament_Name,Game_ID,Tournament_Date,Has_Novelty,
                      Ground_Truth,Novelty_Detected,Novelty_Detected_Step, Novelty_Detected_Time, Reward_Score,Total_Step_Cost,
                      Total_Steps,Total_Time,Time_Start,
                      Time_End,Task_Complete,Game_End_Condition,Pal_Log_Blob_URL,Agent_Log_Blob_URL,Debug_Log_Blob_URL) 
                      VALUES ({', '.join(['?' for i in dictionary_as_tuple_list[0]])}) ; 
                                    """, dictionary_as_tuple_list)

                self.sql_connection.commit()
                self.debug_log.message(f"Scores sent! Game: {game_id}")
            except Exception as e:
                self.debug_log.message(f"Error! Scores not sent: {str(e)}")

    def _update_log_entry(self, game_id, logType, path):
        """
        Update the SQL Results Table to add the Blob URL for a specific log that was successfully uploaded
        :param game_id: Game ID of the log being uploaded
        :param logType: Log Type of the log (to ensure that the right column in the table gets updated)
        :param path: BLOB URL of the Log
        """
        if self.configs is None:
            return None

        if "debug" in logType.lower():
            var_to_adjust = 'Debug_Log_Blob_URL'
        elif "agent" in logType.lower():
            var_to_adjust = 'Agent_Log_Blob_URL'
        elif "pal" in logType.lower():
            var_to_adjust = 'Pal_Log_Blob_URL'
        else:
            self.debug_log.message(f"Unknown Log Type. Schema Update for DB may be required: {logType}")
            return None

        # Using the ? approach automatically escapes strings to be "SQL" safe. Would recommend! :)
        self.cursor.execute(f"""
            UPDATE RESULTS_TEST
            SET {var_to_adjust} = ?
            WHERE   Tournament_Name = ? AND
                    Agent_Name = ? AND
                    Game_ID = {game_id}
            """, (path, CONFIG.TOURNAMENT_ID, CONFIG.AGENT_ID))

        self.sql_connection.commit()

    def upload_pal_messenger_logs(self, palMessenger, game_id, log_type, container=None):
        """
        Uploads the Log to the Azure Blob.
        :param palMessenger: log to upload
        :param game_id: game for this log - used to update the SQL results entry with the log's blob URL
        :param log_type: used the update the SQL result_score entry, ensuring URL is assigned to the right log type
        :param container: container in Azure to upload the blob (default is log-container)

        """
        uploaded_path = self.upload_game_log(palMessenger.log_file, game_id, container)
        if uploaded_path is not None:
            self._update_log_entry(game_id, log_type, uploaded_path)

    def upload_game_log(self, filepath, game_id, container=None):
        """
        Uploads file to the Azure Blob, using a secret key as defined in a separate file.
        Acquire the SecretKey from AzureStorage, if needed
        TODO: Confirm that this works on Windows
        :param filepath: PosixPath object containing a path to the file. use filepath.name to get the file name
        :param game_id: ID of game being uploaded. Used as part of the blob file name to uniquely ID the log.
        :param container: name of container to be uploaded to. If None, defaults to using self.container_name
        :return: True if a file was successfully uploaded to the Azure Blob. False otherwise.
        """
        if self.blob_service_client is not None:
            if container is not None:
                container_to_use = container
            else:
                container_to_use = self.container_name
            blob_name = f"{CONFIG.TOURNAMENT_ID}_{CONFIG.AGENT_ID}_{game_id}_{filepath.name}"
            blob_client = self.blob_service_client.get_blob_client(container=container_to_use, blob=blob_name)
            try:
                with open(filepath, 'rb') as data:
                    blob_client.upload_blob(data)
                    return blob_client.url
            except ServiceRequestError as e:
                self.debug_log.message(f"Service Request Error - something wonky happened during file upload: {str(e)}")
                return None
            except FileNotFoundError:
                self.debug_log.message(f"Error: File not found! {filepath}")
                return None

        else:
            self.debug_log.message("ERROR: blob service client is null. Upload incomplete.")
            return None


if __name__ == '__main__':
    azc = AzureConnectionService(PalMessenger(True, False))
    print(azc.is_connected())