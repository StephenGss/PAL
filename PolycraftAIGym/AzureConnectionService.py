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
        self.valid_connection = False
        self.sql_connection = self._get_sql_connection()
        self.cursor = None
        if self.is_connected():
            self.cursor = self.sql_connection.cursor()

    def _check_for_configs(self):
        if path.exists("../secret_real.ini"):
            configs = configparser.ConfigParser()
            configs.read("../secret_real.ini")
            return configs
        else:
            return None

    @staticmethod
    def _validate_db_connection(dbcon):
        if dbcon is not None:
            dbcur = dbcon.cursor()
            dbcur.execute("""
                                SELECT COUNT(*)
                                FROM information_schema.tables
                                """)
            result = dbcur.fetchone()
            if result:
                # dbcur.close()
                return True
            # dbcur.close()
        return False

    def is_connected(self):
        if self.blob_service_client is not None and self.sql_connection is not None and self.valid_connection:
            return True
        return False

    def _get_sql_connection(self):
        if self.configs is None:
            return None
        Driver = "{ODBC Driver 17 for SQL Server}"
        Server = "tcp:polycraft.database.windows.net,1433"
        Database = "tournament_database"
        Uid = self.configs['azure']['SQL_USERNAME']
        Pwd = self.configs['azure']['SQL_PASSWORD']
        Encrypt = "yes"
        TrustServerCertificate = "yes"
        ConnectionTimeout = 30
        cxn = f'Driver={Driver};Server={Server};Database={Database};Uid={Uid};Pwd={Pwd};Encrypt={Encrypt};TrustServerCertificate={TrustServerCertificate};Connection Timeout={ConnectionTimeout};'
        try:
            db = pyodbc.connect(cxn)
            self.valid_connection = AzureConnectionService._validate_db_connection(db)
            return db
        except Exception as e:
            self.debug_log.message("Error in SQL Connection: " + str(e))
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

    def checkTableExists(self, tablename):
        if not self.is_connected():
            return False
        dbcur = self.sql_connection.cursor()
        dbcur.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = '{0}'
            """.format(tablename.replace('\'', '\'\'')))
        if dbcur.fetchone()[0] == 1:
            # dbcur.close()
            return True

        # dbcur.close()
        return False

    def _create_agent_table_named(self, name):
        if not self.is_connected():
            return False
        try:
            dbcur = self.sql_connection.cursor()
            dbcur.execute(f"""
            CREATE TABLE {name} (
                Tournament_Name VARCHAR(50) not null,
                Game_ID INT not null,
                Step_Number INT not null,
                Time_Stamp VARCHAR (32) not null,
                Step_Cost FLOAT(24),
                Running_Step_Cost FLOAT(24),
                Running_Total_Reward FLOAT(24),
                Goal_Type VARCHAR(32),
                Goal_Achieved BIT,
                Command VARCHAR(50),
                Command_Argument TEXT,
                Command_Result TEXT,
                Command_Message TEXT,
                Game_Over BIT,
                Novelty_Flag TEXT,
                PRIMARY KEY (Tournament_Name, Game_ID, Step_Number)
                );
             """)
            self.sql_connection.commit()
            dbcur.close()
            self.debug_log.message(f"New Table created! Named: {name}")
        except Exception as e:
            self.debug_log.message(f"Error! Table could not be created: {str(e)}")

    def send_game_details_to_azure(self, game_dict, game_id):
        if self.configs is None:
            self.debug_log.message("No Config File available for SQL Connection")
            return None

        if not self.checkTableExists(CONFIG.AGENT_ID):
            # TODO: Replace spaces in agent name with underscores and trim to 32 char for SQL table names
            self._create_agent_table_named(CONFIG.AGENT_ID)

        all_vals = OrderedDict()
        for step in game_dict.keys():
            vals = OrderedDict()
            vals['Tournament_Name'] = str(CONFIG.TOURNAMENT_ID)
            vals['Game_ID'] = int(game_id)
            vals['Step_Number'] = int(step)
            vals['Time_Stamp'] = str(game_dict[step]['Time_Stamp'])
            vals['Step_Cost'] = float(game_dict[step]['stepCost']) * -1  # Make these values negative
            vals['Running_Step_Cost'] = float(game_dict[step]['running_total_cost']) * -1  # make these values negative
            vals['Running_Total_Reward'] = float(game_dict[step]['running_total_score'])
            vals['Goal_Type'] = str(game_dict[step]['goalType'])
            vals['Goal_Achieved'] = str(game_dict[step]['goalAchieved'])
            vals['Command'] = str(game_dict[step]['command'])
            vals['Command_Argument'] = str(game_dict[step]['argument'])
            vals['Command_Result'] = str(game_dict[step]['result'])
            vals['Command_Message'] = str(game_dict[step]['message'])
            vals['Game_Over'] = distutils.util.strtobool(str(game_dict[step]['Game_Over']))
            vals['Novelty_Flag'] = str(game_dict[step]['Distribution'])

            all_vals.update({step: vals})

        rows_to_add = []
        for dict in all_vals.values():
            rows_to_add.extend([tuple(dict.values())])

        self.debug_log.message(f"Sending Game Details to SQL: {rows_to_add}")

        try:
            self.cursor = self.sql_connection.cursor()
            self.cursor.executemany(f"""
                INSERT INTO {CONFIG.AGENT_ID} (
                    {', '.join([i for i in all_vals[1].keys()])}
                    ) 
                  VALUES ({', '.join(['?' for i in rows_to_add[0]])}) ; 
                                """, rows_to_add)

            self.sql_connection.commit()
            self.debug_log.message(f"Game sent! Game: {game_id}")
        except Exception as e:
            self.debug_log.message(f"Error! Scores not sent: {str(e)}")

    def send_summary_to_azure(self, score_dict, game_id):
        """
        CREATE TABLE TOURNAMENT_AGGREGATE (
Task_Name VARCHAR(50) not null,
Agent_Name VARCHAR(50) not null,
Tournament_Name VARCHAR(50) not null,
Game_ID INT not null,
Has_Novelty BIT DEFAULT 0,
Ground_Truth BIT DEFAULT 0,
Novelty_Detected BIT DEFAULT 0,
Novelty_Detected_Step INT,
Novelty_Detected_Time VARCHAR(50),
Game_End_Condition TEXT,
Pal_Log_Blob_URL Text,
Agent_Log_Blob_URL TEXT,
Debug_Log_Blob_URL Text,
        :param score_dict:
        :param game_id:
        :return:
        """
        if self.configs is None:
            self.debug_log.message("No Config File available for SQL Connection")
            return None

        vals = OrderedDict()
        vals['Task_Name'] = str(score_dict[game_id]['game_path'])
        vals['Agent_Name'] = str(CONFIG.AGENT_ID)
        vals['Tournament_Name'] = str(CONFIG.TOURNAMENT_ID)
        vals['Game_ID'] = int(game_id)
        # vals['TournamentDate'] = PalMessenger.time_now_str()
        vals['Has_Novelty'] = int(score_dict[game_id]['novelty'])
        vals['Ground_Truth'] = int(score_dict[game_id]['groundTruth'])
        vals['Novelty_Detected'] = int(score_dict[game_id]['noveltyDetect'])
        vals['Novelty_Detected_Step'] = int(score_dict[game_id]['noveltyDetectStep'])
        vals['Novelty_Detected_Time'] = str(score_dict[game_id]['noveltyDetectTime'])
        vals['Game_End_Condition'] = str(score_dict[game_id]['success_detail'])
        vals['Pal_Log_Blob_URL'] = ""
        vals['Agent_Log_Blob_URL'] = ""
        vals['Debug_Log_Blob_URL'] = ""

        dictionary_as_tuple_list = [tuple(vals.values())]
        self.debug_log.message(f"Sending Score to SQL: {dictionary_as_tuple_list}")
        try:
            self.cursor.executemany(f"""
                            INSERT INTO TOURNAMENT_AGGREGATE ({', '.join([k for k in vals.keys()])}) 
                              VALUES ({', '.join(['?' for i in dictionary_as_tuple_list[0]])}) ; 
                                            """, dictionary_as_tuple_list)

            self.sql_connection.commit()
            self.debug_log.message(f"Game summary sent! Game: {game_id}")
        except Exception as e:
            self.debug_log.message(f"Error! Scores not sent: {str(e)}")

    def send_score_to_azure(self, score_dict, game_id):
        if self.configs is None:
            self.debug_log.message("No Config File available for SQL Connection")
            return None

        vals = OrderedDict()
        # vals['Task_Name'] = CONFIG.GAMES[game_id]
        vals['Task_Name'] = str(score_dict[game_id]['game_path'])
        vals['Agent_Name'] = str(CONFIG.AGENT_ID)
        vals['TournamentNm'] = str(CONFIG.TOURNAMENT_ID)
        vals['Game'] = int(game_id)
        vals['TournamentDate'] = PalMessenger.time_now_str()
        vals['NoveltyFlag'] = int(score_dict[game_id]['novelty'])
        vals['GroundTruth'] = int(score_dict[game_id]['groundTruth'])
        vals['NoveltyDetected'] = int(score_dict[game_id]['noveltyDetect'])
        vals['NoveltyDetectStep'] = int(score_dict[game_id]['noveltyDetectStep'])
        vals['NoveltyDetectTime'] = str(score_dict[game_id]['noveltyDetectTime'])
        # vals['Reward'] = float(score_dict[game_id]['adjustedReward'])
        if distutils.util.strtobool(str(score_dict[game_id]['success'])):
            vals['Reward'] = 256000.0 - float(score_dict[game_id]['totalCost'])
        else:
            vals['Reward'] = float(score_dict[game_id]['totalCost']) * -1
        # vals['Reward'] = float(score_dict[game_id]['adjustedReward'])
        vals['Total_Step_Cost'] = float(score_dict[game_id]['totalCost'])
        vals['Total_Steps'] = float(score_dict[game_id]['step'])
        vals['Total_Time'] = float(score_dict[game_id]['elapsed_time'])
        vals['StartTime'] = str(score_dict[game_id]['startTime'])
        vals['EndTime'] = str(score_dict[game_id]['endTime'])
        vals['Complete'] = distutils.util.strtobool(str(score_dict[game_id]['success']))
        vals['Reason'] = str(score_dict[game_id]['success_detail'])
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
            UPDATE TOURNAMENT_AGGREGATE
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
            self.debug_log.message(f"Log file uploaded: {log_type}")
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
