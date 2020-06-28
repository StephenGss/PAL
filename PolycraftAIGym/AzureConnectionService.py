from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.cosmosdb.table.tableservice import TableService
from azure.cosmosdb.table.models import Entity
import os, time
from os import path
import re
import pyodbc
import config as CONFIG
from collections import OrderedDict
import distutils, distutils.util
from PalMessenger import PalMessenger
from azure.core.exceptions import ServiceRequestError, ServiceRequestTimeoutError, ServiceResponseError
import configparser
import gzip
from filelock import Timeout, FileLock


class AzureConnectionService:

    def __init__(self, debug_log, container_name='round2-logs'):
        self.configs = self._check_for_configs()
        self.debug_log = debug_log
        self.container_name = container_name
        self.blob_service_client = self._read_secret_key()
        self.temp_logs_path = "upload_logs_scripts.sql"
        self.lock = FileLock(f"{self.temp_logs_path}.lock")
        self.valid_connection = False
        self.sql_connection = self._get_sql_connection()
        self.cursor = None
        self.max_retries = 10
        if self.is_connected():
            self.cursor = self.sql_connection.cursor()

    def _check_for_configs(self):
        """
        Checks for the config file: "secret_real.ini". If this file does not exist, a SQL connection is not attempted.
        :return:
        """
        if path.exists("../secret_real.ini"):
            configs = configparser.ConfigParser()
            configs.read("../secret_real.ini")
            return configs
        else:
            return None

    @staticmethod
    def _validate_db_connection(dbcon):
        """
        Queries a count of tables in the database to confirm whether or not a successful connection exists.
        :param dbcon:
        :return:
        """
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
        """
        :return: True if a valid connection exists to the SQL Database.
        """
        if self.blob_service_client is not None and self.sql_connection is not None and self.valid_connection:
            return True
        return False

    def _get_sql_connection(self):
        """
        Connects to the SQL Database if a valid configs file is provided
        :return: pyodbc.SQL_CONNECTION object if a connection is valid. None if an error occurs.
        """
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
            db = pyodbc.connect(cxn, autocommit=True)
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
        """
        Checks if tablename exists in the SQL Database - used to confirm if an Agent Table needs to be created for a new Agent
        :param tablename: name of table to check
        :return: True if a Table exists, False if it does not or if a Table cannot be constructed.
        """
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
        """
        Creates an Agent Table if it does not already exist.
        #TODO: Convert this to a stored procedure that can be invoked with a simpler call
        :param name: Name of Agent Table
        """
        if not self.is_connected():
            return False
        try:
            dbcur = self.sql_connection.cursor()
            dbcur.execute(f"""
            CREATE TABLE {name} (
                Tournament_Name VARCHAR(128) not null,
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
            self.debug_log.message(f"New Table created! Named: {name}")
            dbcur.execute(f"""
            exec build_agent_result_view {name};
            """)
            self.sql_connection.commit()
            dbcur.close()
            self.debug_log.message(f"Agent result view created! Named: {name}_Results_View")
        except Exception as e:
            self.debug_log.message(f"Error! Table could not be created: {str(e)}")

    def send_game_details_to_azure(self, game_dict, game_id):
        """
        Send step-by-step game information to the Agent-Specific Table, Creating the Agent-Specific Table if the
        Agent_ID does not exist.
        :param game_dict: dictionary containing all of the step-keyed information (see :func:~LaunchTournament._record_score() )
        :param game_id: ID of the game whose scores we're uploading

        """
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

        # Check to see if any steps were taken to prevent PKEY errors
        if len(rows_to_add) == 0:
            self.debug_log.message(f"Not Sending Game Details - No Steps Taken!: {rows_to_add}")
            return

        self.debug_log.message(f"Sending Game Details to SQL: {rows_to_add}")

        count = 0
        while count < self.max_retries:
            try:
                count += 1
                self.cursor = self.sql_connection.cursor()
                self.cursor.executemany(f"""
                    INSERT INTO {CONFIG.AGENT_ID} (
                        {', '.join([i for i in all_vals[1].keys()])}
                        ) 
                      VALUES ({', '.join(['?' for i in rows_to_add[0]])}) ; 
                                    """, rows_to_add)

                self.sql_connection.commit()
                self.debug_log.message(f"Game sent! Game: {game_id}")
                break
            except Exception as e:
                time.sleep(1)
                self.debug_log.message(f"Error! Scores not sent: {str(e)}")
                self.debug_log.message(f"retrying... ({count})")

        if count >= self.max_retries:
            self.debug_log.message(
                f"ERROR: Unable to Update {CONFIG.AGENT_ID}. Offending Game: {game_id}")

    def send_summary_to_azure(self, score_dict, game_id):
        """
        Send a summary view to the Tournament_Aggregate Table of the Game Results (one record per game per tournament per agent)
        :param score_dict: Data to be sent
        :param game_id: Game ID for this data
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
        count = 0
        while count < self.max_retries:
            try:
                count += 1
                self.cursor.executemany(f"""
                                INSERT INTO TOURNAMENT_AGGREGATE ({', '.join([k for k in vals.keys()])}) 
                                  VALUES ({', '.join(['?' for i in dictionary_as_tuple_list[0]])}) ; 
                                                """, dictionary_as_tuple_list)

                self.sql_connection.commit()
                self.debug_log.message(f"Game summary sent! Game: {game_id}")
                break
            except Exception as e:
                time.sleep(1)
                self.debug_log.message(f"Error! Scores not sent: {str(e)}")
                self.debug_log.message(f"retrying... ({count})")

        if count >= self.max_retries:
            self.debug_log.message(f"ERROR: Unable to Update TOURNAMENT_AGGREGATE. Offending Game: {game_id}, Tournament: {CONFIG.TOURNAMENT_ID}")

    def threaded_update_logs(self):
        """
        Theaded Function to update TOURNAMENT_AGGREGATE with location of log files in a periodic manner

        Every 1.5x CONFIG.MAX_TIME seconds, this function reads all SQL statements generated by
        self._update_log_entry in the temp_logs_path file and executes them.
        :return:
        """
        if not os.path.exists(self.temp_logs_path):
            with open(self.temp_logs_path, 'a') as wf:
                wf.write('')
        else:
            self.debug_log.message("File already exists? Strange...")

        should_continue = True
        max_retries = 3
        try_counter = 0
        global_upload_count = 0
        self.debug_log.message("Thread Initialized.")
        while should_continue:
            time.sleep(CONFIG.MAX_TIME*2.5)  # Run every 1.5 max-time game cycles (TODO: increase this?)
            upload_count = 0
            self.debug_log.message("Attempting Upload...")
            with self.lock.acquire():
                try:
                    with open(self.temp_logs_path, 'r') as rf:  # This file is "touched" above
                        a = rf.read()
                        e = a.split(';')
                        for item in e:
                            if 'UPDATE' not in item:
                                continue
                            # self.debug_log.message(item)
                            upload_count += 1
                            with self.sql_connection.cursor() as cursor:
                                cursor.execute(f"""{item}""")
                            self.sql_connection.commit()
                    os.remove(self.temp_logs_path)          # File deleted in this thread
                except FileNotFoundError as e:
                    self.debug_log.message("ALERT: File not found. Main Thread over. (Double-incrementing try_counter)")
                    try_counter += 2
                except Exception as e:
                    with open(self.temp_logs_path, 'r') as rf, open(f"{self.temp_logs_path}.err", 'a') as wf:
                        wf.write(rf.read())
                    self.debug_log.message(f"ERROR: Cannot Upload! Temp saving file and moving on. PLease re-run manually: {self.temp_logs_path}.err\n {str(e)}")

            global_upload_count += upload_count
            self.debug_log.message(f"Uploaded {upload_count} Logs for {(upload_count/3)} games. Running total: {global_upload_count}")
            if upload_count == 0:
                try_counter += 1
            if try_counter >= max_retries:
                should_continue = False

        self.debug_log.message(f"Update Thread completed. Total updates: {global_upload_count}")

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

        # update the file containing who all should be uploaded
        with self.lock.acquire():
            with open(f"{self.temp_logs_path}", 'a') as file:
                upload_stmt = f"""
                    UPDATE TOURNAMENT_AGGREGATE
                    SET {var_to_adjust} = '{path}'
                    WHERE   Tournament_Name = '{CONFIG.TOURNAMENT_ID}' AND
                            Agent_Name = '{CONFIG.AGENT_ID}' AND
                            Game_ID = {game_id}
                    ;"""
                file.write(f"{upload_stmt}")

        # Using the ? approach automatically escapes strings to be "SQL" safe. Would recommend! :)
        # For now, try uploading no more than 5 times
        # count = 0
        # while count < self.max_retries:
        #     try:
        #         count += 1
        #         self.cursor.execute(f"""
        #             UPDATE TOURNAMENT_AGGREGATE
        #             SET {var_to_adjust} = ?
        #             WHERE   Tournament_Name = ? AND
        #                     Agent_Name = ? AND
        #                     Game_ID = {game_id}
        #             """, (path, CONFIG.TOURNAMENT_ID, CONFIG.AGENT_ID))
        #         self.sql_connection.commit()
        #         break
        #     except Exception as e:
        #         time.sleep(1)
        #         self.debug_log.message(f"MSSQL Simultaneous Upload Lock - retrying... ({count})\n" + str(e))
        #
        # # Print an error letting user know upload failed (print to debug log for now, even if it's already uploaded)
        # if count >= self.max_retries:
        #     self.debug_log.message(f"ERROR: Unable to Update TOURNAMENT_AGGREGATE. Offending Game: {game_id}, Tournament: {CONFIG.TOURNAMENT_ID}, Variable: {var_to_adjust}")

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

    def _compress_log_file(self, uncompressed_file):
        """
        Compresses a log file
        :param uncompressed_file: a valid, uncompressed log file path
        :return: a compressed log file
        """
        fzip = None
        # Zip File
        if path.exists(uncompressed_file):
            with open(uncompressed_file, 'rb') as orig_file, gzip.open(f'{uncompressed_file}.gz', 'wb') as zipped_file:
                    zipped_file.writelines(orig_file)
                    fzip = zipped_file

            # Delete unzipped file
            os.remove(uncompressed_file)

        if fzip is not None:
            return fzip.filename
        return None


    def upload_game_log(self, filepath, game_id, container=None):
        """
        Uploads file to the Azure Blob, using a secret key as defined in a separate file.
        Acquire the SecretKey from AzureStorage, if needed
        noTODO: Confirm that this works on Windows -- Not necessary as OS preference is UNIX.
        :param filepath: PosixPath object containing a path to the file. use filepath.name to get the file name
        :param game_id: ID of game being uploaded. Used as part of the blob file name to uniquely ID the log.
        :param container: name of container to be uploaded to. If None, defaults to using self.container_name
        :return: URL of uploaded path if successfully uploaded to Blob; None otherwise.
        """
        # Check to see if file path is valid before attempting to upload.
        if not filepath or not path.exists(filepath):
            self.debug_log.message(f"Log not found - not sending to Azure: {filepath}")
            return None

        # zip the file
        filepath = self._compress_log_file(filepath)

        if self.blob_service_client is not None:
            if container is not None:
                container_to_use = container
            else:
                container_to_use = self.container_name
            blob_name = f"{CONFIG.TOURNAMENT_ID}_{CONFIG.AGENT_ID}_{game_id}_{filepath}"
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
