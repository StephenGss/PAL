# sample2_pools_and_resourcefiles.py Code Sample
#
# Copyright (c) Microsoft Corporation
#
# All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# from __future__ import print_function

try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import datetime
import os, re

import azure.storage.blob as azureblob
import azure.batch._batch_service_client as batch
import azure.batch.batch_auth as batchauth
import azure.batch.models as batchmodels

import PolycraftAIGym.common.helpers as helpers
from AzureBatch.AgentBatchCommands import AgentType, AgentBatchCommands

_CONTAINER_NAME = 'batch-workflow-fog-of-war'

DEBUG_FLAG = False

### SIFT ###
SIFT_APPLICATION_ID = 'agent_sift'
SIFT_APPLICATION_VERSION = '14'
APPLICATION_ID_FIXED = 'agent_sift'
APPLICATION_DIR = '$AZ_BATCH_APP_PACKAGE_' + APPLICATION_ID_FIXED + '_' + SIFT_APPLICATION_VERSION

### TUFTS ###
TUFT_APPLICATION_ID = 'agent_tufts'
TUFT_VERSION = '5'
TUFT_APPLICATION_DIR = '$AZ_BATCH_APP_PACKAGE_' + TUFT_APPLICATION_ID + '_' + TUFT_VERSION
### GT ###
GT_APP_ID = 'agent_gt_pogo'
GT_APPLICATION_VERSION = '6'
GT_APPLICATION_DIR = '$AZ_BATCH_APP_PACKAGE_' + GT_APP_ID + '_' + GT_APPLICATION_VERSION

### GT Plan ###
GT_PLAN_APP_ID = 'agent_gt_pogo_planner'
GT_PLAN_APPLICATION_VERSION = '1'
GT_PLAN_APPLICATION_DIR = '$AZ_BATCH_APP_PACKAGE_' + GT_PLAN_APP_ID + '_' + GT_PLAN_APPLICATION_VERSION


### GT HG ###
GT_HUGA_APP_ID = 'agent_gt_huga_1'
GT_HUGA_APP_VERSION = '1'
GT_HUGA_APP_DIR = '$AZ_BATCH_APP_PACKAGE_' + GT_HUGA_APP_ID + '_' + GT_HUGA_APP_VERSION

### GT HG MATLAB ###
GT_HUGA_MLAB_APP_ID = 'agent_gt_huga_matlab'
GT_HUGA_MLAB_APP_VERSION = '1'
GT_HUGA_MLAB_APP_DIR = '$AZ_BATCH_APP_PACKAGE_' + GT_HUGA_MLAB_APP_ID + '_' + GT_HUGA_MLAB_APP_VERSION

### SRI ###
SRI_APP_ID = 'agent_sri'
SRI_VERSION = '5'
SRI_APPLICATION_DIR = '$AZ_BATCH_APP_PACKAGE_' + SRI_APP_ID + '_' + SRI_VERSION

### RAYTHEON ###
RAYTHEON_APP_ID = 'agent_raytheon'  # APP ID
RAYTHEON_VERSION = '12'
RAYTHEON_APPLICATION_DIR = '$AZ_BATCH_APP_PACKAGE_' + RAYTHEON_APP_ID + '_' + RAYTHEON_VERSION

### CRA ###
CRA_APP_ID = 'agent_cra'  # APP ID
CRA_VERSION = '4'
CRA_APPLICATION_DIR = '$AZ_BATCH_APP_PACKAGE_' + CRA_APP_ID + '_' + CRA_VERSION

APP_DICT = {'agent_sift': APPLICATION_DIR,
            'agent_tufts': TUFT_APPLICATION_DIR,
            'agent_gt_pogo': GT_APPLICATION_DIR,
            'agent_sri': SRI_APPLICATION_DIR,
            'agent_gt_huga_1': GT_HUGA_APP_DIR,
            'agent_gt_huga_matlab': GT_HUGA_MLAB_APP_DIR,
            'agent_gt_pogo_planner': GT_PLAN_APPLICATION_DIR,
            'agent_raytheon': RAYTHEON_APPLICATION_DIR,
            'agent_cra': CRA_APPLICATION_DIR,
            }

# _SIMPLE_TASK_NAME = 'simple_task.py'
# _SIMPLE_TASK_PATH = os.path.join('resources', 'simple_task.py')


class AzureBatchLaunchTournaments:

    def __init__(self, agent_name, agent_type, library_of_tournaments, global_config, pool, suffix=None):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.suffix = suffix
        self.pool = pool
        self.library_of_tournaments = library_of_tournaments
        self.global_config = global_config
        self.agent_commands = AgentBatchCommands(APP_DICT, self.agent_name, self.agent_type)
        # later self.commands = AgentBatchCommands.AgentBatchCommands(self.agent_name, self.agent_type, )

    def create_pool(self, batch_client, block_blob_client, vm_size, pool_id, vm_count):
        """Creates an Azure Batch pool with the specified id.

        :param batch_client: The batch client to use.
        :type batch_client: `batchserviceclient.BatchServiceClient`
        :param block_blob_client: The storage block blob client to use.
        :type block_blob_client: `azure.storage.blob.BlockBlobService`
        :param str pool_id: The id of the pool to create.
        :param str vm_size: vm size (sku)
        :param int vm_count: number of vms to allocate
        """
        # pick the latest supported 16.04 sku for UbuntuServer
        sku_to_use, image_ref_to_use = \
            helpers.select_latest_verified_vm_image_with_node_agent_sku(
                batch_client, 'Canonical', 'UbuntuServer', '18.04')

        block_blob_client.create_container(_CONTAINER_NAME, fail_on_exist=False)


        application_package_references = [
            # batchmodels.ApplicationPackageReference(application_id=SIFT_APPLICATION_ID, version=SIFT_APPLICATION_VERSION),
            batchmodels.ApplicationPackageReference(application_id=TUFT_APPLICATION_ID, version=TUFT_VERSION),
            # batchmodels.ApplicationPackageReference(application_id=GT_APP_ID, version=GT_APPLICATION_VERSION),
            # batchmodels.ApplicationPackageReference(application_id=SRI_APP_ID, version=SRI_VERSION),
            # batchmodels.ApplicationPackageReference(application_id=GT_HUGA_APP_ID, version=GT_HUGA_APP_VERSION),
            # batchmodels.ApplicationPackageReference(application_id=GT_HUGA_MLAB_APP_ID, version=GT_HUGA_MLAB_APP_VERSION),
            # batchmodels.ApplicationPackageReference(application_id=GT_PLAN_APP_ID, version=GT_PLAN_APPLICATION_VERSION),
            # batchmodels.ApplicationPackageReference(application_id=RAYTHEON_APP_ID, version=RAYTHEON_VERSION),
            # batchmodels.ApplicationPackageReference(application_id=CRA_APP_ID, version=CRA_VERSION),
        ]

        # Create User Accounts
        users = [
            batchmodels.UserAccount(
                name='azureuser',
                password='adminAcct$1',
                elevation_level=batchmodels.ElevationLevel.admin),
            # batchmodels.UserAccount(
            #     name='pool-nonadmin',
            #     password='******',
            #     elevation_level=batchmodels.ElevationLevel.non_admin)
        ]

        pool = batchmodels.PoolAddParameter(
            id=pool_id,
            virtual_machine_configuration=batchmodels.VirtualMachineConfiguration(
                image_reference=batchmodels.ImageReference(
                    publisher="Canonical",
                    offer="UbuntuServer",
                    sku="18.04-LTS",
                    version="latest"
                ),
                node_agent_sku_id="batch.node.ubuntu 18.04"),
            vm_size=vm_size,
            user_accounts=users,
            target_dedicated_nodes=vm_count,
            application_package_references=application_package_references,

            # mount_configuration=[batch.models.MountConfiguration(
            #     azure_file_share_configuration=batch.models.AzureFileShareConfiguration(
            #         account_name=global_config.get('Storage', 'storageaccountname'),
            #         azure_file_url="https://polycrafttournamentdata.file.core.windows.net/pal-sift",
            #         account_key=global_config.get('Storage', 'storageaccountkey'),
            #         relative_mount_path='sift_file_share')
            #     ),
            # ],


            start_task=batchmodels.StartTask(
                command_line=helpers.wrap_commands_in_shell('linux', [
                    'whoami',
                    'usermod -aG sudo azureuser',  # Run the setup scripts as ROOT and add azureuser to the sudoers file
                    'apt-get install software-properties-common',
                    # causes issues if this is run as azureuser? see: https://askubuntu.com/questions/1109982/e-could-not-get-lock-var-lib-dpkg-lock-frontend-open-11-resource-temporari
                    'apt-add-repository universe',
                    'apt-get update',
                    'apt-get update && apt-get install cifs-utils && sudo mkdir -p /mnt/PolycraftFileShare',
                    f'mount -t cifs //polycrafttournamentdata.file.core.windows.net/pal-sift /mnt/PolycraftFileShare -o vers=3.0,username={self.global_config.get("Storage", "storageaccountname")},password={self.global_config.get("Storage", "storageaccountkey")},dir_mode=0777,file_mode=0777,serverino && ls /mnt/PolycraftFileShare',
                    'mkdir ~/matlab && cp /mnt/PolycraftFileShare/setup/MATLAB_Runtime_R2020a_Update_2_glnxa64.zip ~/matlab/',
                    'cd ~/matlab',
                    'apt install unzip -y',
                    'unzip MATLAB_Runtime_R2020a_Update_2_glnxa64.zip',
                    './install -mode silent -agreeToLicense yes',
                    'export LD_LIBRARY_PATH=/usr/local/MATLAB/MATLAB_Runtime/v98/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v98/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v98/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v98/extern/bin/glnxa64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}',
                    # 'sudo apt-get install -y python3-pip'
                ]),
                # TODO: include add'l resource files for initial startup
                wait_for_success=True,
                # user_accounts=users,
                user_identity=batchmodels.UserIdentity(
                    # user_name='azureuser',
                    auto_user=batchmodels.AutoUserSpecification(
                        scope=batchmodels.AutoUserScope.pool,
                        elevation_level=batchmodels.ElevationLevel.admin)
                    # ),

                ),

            ),
        )

        helpers.create_pool_if_not_exist(batch_client, pool)

    def submit_job_and_add_task(self, batch_client, block_blob_client, job_id, pool_id):
        """Submits a job to the Azure Batch service and adds
        a task that runs a python script.

        :param batch_client: The batch client to use.
        :type batch_client: `batchserviceclient.BatchServiceClient`
        :param block_blob_client: The storage block blob client to use.
        :type block_blob_client: `azure.storage.blob.BlockBlobService`
        :param str job_id: The id of the job to create.
        :param str pool_id: The id of the pool to use.
        """
        job = batchmodels.JobAddParameter(
            id=job_id,
            pool_info=batchmodels.PoolInformation(pool_id=pool_id),
            on_all_tasks_complete='terminateJob',
        )

        batch_client.job.add(job)

        block_blob_client.create_container(
            _CONTAINER_NAME,
            fail_on_exist=False)

        # os.chdir('../output/')
        count = 0
        maxCount = 1  # TODO: move this.
        for file in os.listdir(f'{self.library_of_tournaments}'):
            if count >= maxCount and DEBUG_FLAG:
                break
            if not file.endswith(".zip"):
                continue
            filename = file.split('.')[0]

            # Get commands
            cmds = self.agent_commands.get_task_commands(file, filename, self.suffix)

            application_package_references = [
                # batchmodels.ApplicationPackageReference(application_id=SIFT_APPLICATION_ID, version=SIFT_APPLICATION_VERSION),
                batchmodels.ApplicationPackageReference(application_id=TUFT_APPLICATION_ID, version=TUFT_VERSION),
                # batchmodels.ApplicationPackageReference(application_id=GT_APP_ID, version=GT_APPLICATION_VERSION),
                # batchmodels.ApplicationPackageReference(application_id=SRI_APP_ID, version=SRI_VERSION),
                # batchmodels.ApplicationPackageReference(application_id=GT_HUGA_APP_ID, version=GT_HUGA_APP_VERSION),
                # batchmodels.ApplicationPackageReference(application_id=GT_HUGA_MLAB_APP_ID,
                #                                         version=GT_HUGA_MLAB_APP_VERSION),
                # batchmodels.ApplicationPackageReference(application_id=GT_PLAN_APP_ID,
                #                                         version=GT_PLAN_APPLICATION_VERSION),
                # batchmodels.ApplicationPackageReference(application_id=RAYTHEON_APP_ID, version=RAYTHEON_VERSION),
                # batchmodels.ApplicationPackageReference(application_id=CRA_APP_ID, version=CRA_VERSION),
            ]

            user_identity = batch.models.UserIdentity(
                # user_name='azureuser',
                auto_user=batch.models.AutoUserSpecification(
                    scope=batch.models.AutoUserScope.pool,
                    elevation_level=batch.models.ElevationLevel.admin)
            )

            sas_url = helpers.upload_blob_and_create_sas(
                block_blob_client,
                _CONTAINER_NAME,
                'inputs-test/' + file,
                self.library_of_tournaments + file,
                datetime.datetime.utcnow() + datetime.timedelta(weeks=2))

            setup_url = helpers.upload_blob_and_create_sas(
                block_blob_client,
                _CONTAINER_NAME,
                "setup_azure_batch_initial.sh",
                'setup_azure_batch_initial.sh',
                datetime.datetime.utcnow() + datetime.timedelta(weeks=2))

            secret_url = helpers.upload_blob_and_create_sas(
                block_blob_client,
                _CONTAINER_NAME,
                "secret_real.ini",
                '../secret_real.ini',
                datetime.datetime.utcnow() + datetime.timedelta(weeks=2))

            sri_url = helpers.upload_blob_and_create_sas(
                block_blob_client,
                _CONTAINER_NAME,
                "sri_run.sh",
                '../sri_run.sh',
                datetime.datetime.utcnow() + datetime.timedelta(weeks=2))

            sift_wrap = helpers.upload_blob_and_create_sas(
                block_blob_client,
                _CONTAINER_NAME,
                "agents/sift_tournament_agent_launcher.sh",
                '../sift_tournament_agent_launcher.sh',
                datetime.datetime.utcnow() + datetime.timedelta(weeks=2))

            constraint = batchmodels.TaskConstraints(
                retention_time=datetime.timedelta(minutes=1440),
            )

            task = batchmodels.TaskAddParameter(
                id=f"Tournament-{str(count)}-{filename}",
                command_line=helpers.wrap_commands_in_shell('linux', cmds),
                constraints=constraint,
                resource_files=[
                    batchmodels.ResourceFile(
                        file_path=file,
                        http_url=sas_url),
                    batchmodels.ResourceFile(
                        file_path='setup/' + 'setup_azure_batch_initial.sh',
                        http_url=setup_url),
                    batchmodels.ResourceFile(
                        file_path='setup/' + 'sri_run.sh',
                        http_url=sri_url),
                    batchmodels.ResourceFile(
                        file_path='secret_real.ini',
                        http_url=secret_url),
                    batchmodels.ResourceFile(
                        file_path='setup/' + 'sift_tournament_agent_launcher.sh',
                        http_url=sift_wrap),
                ],
                application_package_references=application_package_references,
                user_identity=user_identity)

            batch_client.task.add(job_id=job.id, task=task)

            count += 1

    def execute_sample(self):
        """Executes the sample with the specified configurations.

        :param global_config: The global configuration to use.
        :type global_config: `configparser.ConfigParser`
        :param sample_config: The sample specific configuration to use.
        :type sample_config: `configparser.ConfigParser`
        """
        # Set up the configuration
        batch_account_key = self.global_config.get('Batch', 'batchaccountkey')
        batch_account_name = self.global_config.get('Batch', 'batchaccountname')
        batch_service_url = self.global_config.get('Batch', 'batchserviceurl')

        storage_account_key = self.global_config.get('Storage', 'storageaccountkey')
        storage_account_name = self.global_config.get('Storage', 'storageaccountname')
        storage_account_suffix = self.global_config.get(
            'Storage',
            'storageaccountsuffix')
        storage_account_connection_string = self.global_config.get('Storage', 'storageconnectionstring')

        should_delete_container = self.global_config.getboolean(
            'DEFAULT',
            'shoulddeletecontainer')
        should_delete_job = self.global_config.getboolean(
            'DEFAULT',
            'shoulddeletejob')
        should_delete_pool = self.global_config.getboolean(
            'DEFAULT',
            'shoulddeletepool')
        pool_vm_size = self.global_config.get(
            'DEFAULT',
            'poolvmsize')
        pool_vm_count = self.global_config.getint(
            'DEFAULT',
            'poolvmcount')

        # Print the settings we are running with
        helpers.print_configuration(self.global_config)
        # helpers.print_configuration(sample_config)

        credentials = batchauth.SharedKeyCredentials(
            batch_account_name,
            batch_account_key)
        batch_client = batch.BatchServiceClient(
            credentials,
            batch_url=batch_service_url)

        # Retry 5 times -- default is 3
        batch_client.config.retry_policy.retries = 5

        # azureblob.BlobServiceClient()

        block_blob_client = azureblob.BlockBlobService(
            account_name=storage_account_name,
            account_key=storage_account_key,
            endpoint_suffix=storage_account_suffix)
        # https://pal.centralus.batch.azure.com

        # block_blob_client = azureblob.BlobServiceClient.from_connection_string(
        #     storage_account_connection_string)

        job_id = helpers.generate_unique_resource_name(
            f"{self.agent_name}_Tournaments")
        pool_id = self.pool
        # try:
        self.create_pool(
            batch_client,
            block_blob_client,
            pool_vm_size,
            pool_id,
            pool_vm_count,
            )

        self.submit_job_and_add_task(
            batch_client,
            block_blob_client,
            job_id,
            pool_id,
        )

        # helpers.wait_for_tasks_to_complete(
        #     batch_client,
        #     job_id,
        #     datetime.timedelta(minutes=180))

        tasks = batch_client.task.list(job_id)
        task_ids = [task.id for task in tasks]
        print(task_ids)
            # helpers.print_task_output(batch_client, job_id, task_ids)
        # finally:
        #     # clean up
        #     if should_delete_container:
        #         block_blob_client.delete_container(
        #             _CONTAINER_NAME,
        #             fail_not_exist=False)
        #     if should_delete_job:
        #         print("Deleting job: ", job_id)
        #         batch_client.job.delete(job_id)
        #     if should_delete_pool:
        #         print("Deleting pool: ", pool_id)
        #         batch_client.pool.delete(pool_id)


def launch_tournament_wrapper(agent, agentType, test_type, global_config, pool, suffix, tournament_directory, ):
    """
    Launch Script to kick off a series of Tournaments for a given Agent in a named pool
    Launch ALl tournaments that belong in the same pool using this function

    :param agent: Agent Name (Note: this will create a new Table and View if the agent doesn't already exist)
    :param agentType: Agent Type (Enum - see AgentBatchCommands for valid options)
    :param test_type: See Enum
    :param global_config: Global Config parser object - make sure to create a file called AzureBatch.cfg
    :param pool: name of pool to be created
    :param suffix: Tournament Name suffix (usually, date and hour of execution)
    :param tournament_directory: Location within which to search for all tournament zips
    I.e., all_tournaments_provided/pogo/ will get the zips from all of the sub folders for the right game type
    (i.e. all zips inside a X1000/ folder if TestType.Stage6 is passed in)

    """

    tournaments_to_launch = get_tournaments(test_type, tournament_directory)
    for folder in tournaments_to_launch:
        # pass
        agent_pool = AzureBatchLaunchTournaments(agent, agentType, folder, global_config, pool, suffix)
        agent_pool.execute_sample()


def get_tournaments(test_type,tournament_directory):
    """
    Helper script to iterate through a tournament directory and get all tournament zips of a particular test type
    (i.e. ,TestType.Stage6 will return any zip file within an X1000/ folder.
    :param test_type: Testing Stage - see Enum
    :param tournament_directory: Folder within which to search for zips recursively.
    :return: A list of zips (each zip file is a tournament that will become a task to complete in the parent pool)
    """

    output = []
    for subdir, folders, files in os.walk(f'{tournament_directory}'):
        for file in files:
            if file.endswith('.zip') and test_type.value in file:
                print(f'{subdir}/{file}')
                zip = f'{subdir}/{file}'
                output.append(f'{subdir}/')

    output = list(set(output))
    return output

def launch_pools_per_novelty(agent, agentType, test_type, global_config, pool, suffix, tournament_directory, ):
    r=f'{os.getcwd()}/{tournament_directory}'
    pools = {f'{a}': f'{r}/{a}/' for a in os.listdir(r) if not '.' in a}
    print(pools)
    for pool_name, tournaments in pools.items():
        tournaments_to_launch = get_tournaments(test_type, f'{tournament_directory}{pool_name}/')
        print(f"pool name: {pool}{pool_name}")
        print(tournaments_to_launch)
        for folder in tournaments_to_launch:
            # pass
            agent_pool = AzureBatchLaunchTournaments(agent, agentType, folder, global_config, f"{pool}{pool_name}", suffix)
            agent_pool.execute_sample()


from enum import Enum

class TestType(Enum):
    STAGE4 = "X0010"
    STAGE5 = "X0100"
    STAGE6 = "X1000"



if __name__ == '__main__':
    global_config = configparser.ConfigParser()
    global_config.read(helpers._SAMPLES_CONFIG_FILE_NAME)
    #
    global_config.set('DEFAULT', 'poolvmcount', '3')

    # launch_pools_per_novelty(
    #     "TUFTS_AGENT_TEST_V3",
    #     AgentType.TUFTS,
    #     TestType.STAGE5,
    #     global_config,
    #     pool="POGO_TUFTS_",
    #     suffix="_062622",
    #     tournament_directory="../tournaments/old/tufts_0626_launch/",
    # )
    huga_test_files = f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\huga-12M-tournaments-zipped\\HUGA_V1HUGA_TEST"
    huga_10_files = f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\huga-12M-tournaments-zipped\\HUGA_10game_prenovelty"
    huga_100_files = f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\huga-12M-tournaments-zipped\\HUGA_100game_prenovelty"
    huga_SN10_files = f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\huga-12M-tournaments-zipped\\HUGA_10game_shared_novelty"
    huga_SN100_files = f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\huga-12M-tournaments-zipped\\HUGA_100game_shared_novelty"
    pogo_files = f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\pogo-6M-tournaments-zipped\\POGO_L00_T01_S01"
    pogo_10_files = f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\pogo-12M-tournaments-zipped\\POGO_10game_prenovelty"
    pogo_100_files = f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\pogo-12M-tournaments-zipped\\POGO_100game_prenovelty"
    pogo_SN10_files = f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\pogo-12M-tournaments-zipped\\POGO_10game_shared_novelties"
    pogo_SN100_files = f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\00. 06-12 Months\\98. 12M Tournament Files\\pogo-12M-tournaments-zipped\\POGO_100game_shared_novelties"
    #
    # launch_tournament_wrapper(
    #     agent="SIFT_AGENT_12M_R1125",
    #     agentType=AgentType.SIFT,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_SIFT_SN100_V1",
    #     suffix="_112017",
    #     tournament_directory=pogo_SN100_files,
    # )
    #
    # launch_tournament_wrapper(
    #    "TUFTS_AGENT_12M_V4",
    #    AgentType.TUFTS,
    #    TestType.STAGE5,
    #    global_config,
    #    pool="POGO_TUFTS_VIRGIN_X0100_new1",
    #    suffix="_112711",
    #    tournament_directory=pogo_100_files,
    # )

    # global_config.set('DEFAULT', 'poolvmcount', '12')
    # launch_tournament_wrapper(
    #     "RAYTHEON_AGENT_V7",
    #     AgentType.RAYTHEON,
    #     TestType.STAGE4,
    #     global_config,
    #     pool="RAYTHEON_VIRGIN_X0010_V1",
    #     suffix="_112711",
    #     tournament_directory=huga_10_files,
    # )
    #
    # launch_tournament_wrapper(
    #     agent="CRA_AGENT_12M_V2",
    #     agentType=AgentType.CRA,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_CRA_SN_X0100_v4",
    #     suffix="_112510",
    #     tournament_directory=pogo_SN100_files,
    # )

    # launch_tournament_wrapper(
    #     agent="CRA_AGENT_12M_V1",
    #     agentType=AgentType.CRA,
    #     test_type=TestType.STAGE4,
    #     global_config=global_config,
    #     pool="POGO_CRA_VIRGIN_10_v8",
    #     suffix="_111214",
    #     tournament_directory=pogo_files,
    # )
    #
    # global_config.set('DEFAULT', 'poolvmcount', '12')
    #
    launch_tournament_wrapper(
        agent="SRI_AGENT_12M_V4",
        agentType=AgentType.SRI,
        test_type=TestType.STAGE4,
        global_config=global_config,
        pool="HUGA_SRI_VIRGIN_10_V2",
        suffix="_112711",
        tournament_directory=huga_10_files,
    )

    # launch_tournament_wrapper(
    #     agent="CRA_AGENT_12M_V1",
    #     agentType=AgentType.CRA,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_CRA_VIRGIN_100_v1",
    #     suffix="_111223",
    #     tournament_directory=pogo_files,
    # )

    # launch_tournament_wrapper(
    #     agent="SRI_AGENT_12M_V4",
    #     agentType=AgentType.SRI,
    #     test_type=TestType.STAGE4,
    #     global_config=global_config,
    #     pool="HUGA_SRI_VIRGIN_10_v8",
    #     suffix="_111222",
    #     tournament_directory=huga_files,
    # )

    # launch_tournament_wrapper("GT_AGENT_POGO_PLAN_V1",
    #                           AgentType.GT_POGO_PLAN_BASELINE,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="POGO_GT_PLAN_R2_L1T2",
    #                           suffix="_062622",
    #                           tournament_directory="../tournaments/unknown_all_tournaments_to_TA2/pogo/POGO_L01_T01_S01_AXE/",
    #                           )
    #
    # launch_tournament_wrapper("GT_AGENT_POGO_PLAN_V1",
    #                           AgentType.GT_POGO_PLAN_BASELINE,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="POGO_GT_PLAN_R2_L2",
    #                           suffix="_062622",
    #                           tournament_directory="../tournaments/unknown_all_tournaments_to_TA2/pogo/POGO_L02_T01_S01_TREES/",
    #                           )
    #
    #
    # launch_tournament_wrapper("GT_AGENT_POGO_PLAN_V1",
    #                           AgentType.GT_POGO_PLAN_BASELINE,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="POGO_GT_PLAN_R2_L3",
    #                           suffix="_062622",
    #                           tournament_directory="../tournaments/unknown_all_tournaments_to_TA2/pogo/POGO_L03_T01_S01_FAKE_RECIPE_O/",
    #                           )

    # launch_tournament_wrapper("GT_AGENT_POGO_PLAN_V1"
    #                           AgentType.GT_POGO_PLAN_BASELINE,
    #
    #                           )

    # global_config.set('DEFAULT', 'poolvmcount', '12')
    # #
    # launch_tournament_wrapper("GT_HUGA_MLAB_V1",
    #                           AgentType.GT_HG_BASELINE_MATLAB,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="HUGA_GT_MLAB_L1",
    #                           suffix="_062422",
    #                           tournament_directory="../tournaments/unknown_all_tournaments_to_TA2/huga/HUGA_L01_T02_S02_DETRITUS/")
    #
    # launch_tournament_wrapper("GT_HUGA_MLAB_V1",
    #                           AgentType.GT_HG_BASELINE_MATLAB,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="HUGA_GT_MLAB_L2",
    #                           suffix="_062422",
    #                           tournament_directory="../tournaments/unknown_all_tournaments_to_TA2/huga/HUGA_L02_T01_S01_WALL_COLOR/")
    #
    # launch_tournament_wrapper("GT_HUGA_MLAB_V1",
    #                           AgentType.GT_HG_BASELINE_MATLAB,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="HUGA_GT_MLAB_L3",
    #                           suffix="_062422",
    #                           tournament_directory="../tournaments/unknown_all_tournaments_to_TA2/huga/HUGA_L03_T01_S01_SCREEN_FLIP/")

    # #
    # launch_tournament_wrapper("TUFTS_AGENT_TEST_V3",
    #                           AgentType.TUFTS,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="POGO_TUFTS_R2_L1",
    #                           suffix="_062221",
    #                           tournament_directory="../tournaments/unknown_all_tournaments_to_TA2/pogo/POGO_L01_T01_S01_AXE/",
    #                           )

    # launch_tournament_wrapper("TUFTS_AGENT_TEST_V3",
    #                           AgentType.TUFTS,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="POGO_TUFTS_R2_L2",
    #                           suffix="_062221",
    #                           tournament_directory="../tournaments/unknown_all_tournaments_to_TA2/pogo/POGO_L02_T01_S01_TREES/",
    #                           )
    #

    # launch_tournament_wrapper("TUFTS_AGENT_TEST_V3",
    #                           AgentType.TUFTS,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="POGO_TUFTS_VIRGIN_X100",
    #                           suffix="_062322",
    #                           tournament_directory="../tournaments/unknown_all_tournaments_to_TA2/pogo/POGO_L03_T01_S01_FAKE_RECIPE_O/",
    #                           )

    # launch_tournament_wrapper("TUFTS_AGENT_TEST_V3",
    #                           AgentType.TUFTS,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="POGO_TUFTS_VIRGIN_X100",
    #                           suffix="_062322",
    #                           tournament_directory="../tournaments/pogo_no_novelty/",
    #                           )

   # global_config.set('DEFAULT', 'poolvmcount', '16')

    # launch_tournament_wrapper(
    #     agent="SIFT_AGENT_TEST_V6",
    #     agentType=AgentType.SIFT,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_SIFT_L1_T1_6",
    #     suffix="_062611",
    #     tournament_directory="../tournaments/old/pogo_lvl1a/",
    # )

    # launch_tournament_wrapper(
    #     agent="SIFT_AGENT_TEST_V6",
    #     agentType=AgentType.SIFT,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_SIFT_L1_T1_6b",
    #     suffix="_062611",
    #     tournament_directory="../tournaments/old/pogo_lvl1b/",
    # )

    # global_config.set('DEFAULT', 'poolvmcount', '18')
    #
    # launch_tournament_wrapper(
    #     agent="SIFT_AGENT_TEST_V6",
    #     agentType=AgentType.SIFT,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_SIFT_L2_T1_6",
    #     suffix="_062611",
    #     tournament_directory="../tournaments/old/pogo_lvl2a/",
    # )
    #
    # launch_tournament_wrapper(
    #     agent="SIFT_AGENT_TEST_V6",
    #     agentType=AgentType.SIFT,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_SIFT_L2_T1_6b",
    #     suffix="_062611",
    #     tournament_directory="../tournaments/old/pogo_lvl2b/",
    # )
    #
    # launch_tournament_wrapper(
    #     agent="SIFT_AGENT_TEST_V6",
    #     agentType=AgentType.SIFT,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_SIFT_L3_T1_6",
    #     suffix="_062611",
    #     tournament_directory="../tournaments/old/pogo_lvl3a/",
    # )
    #
    # launch_tournament_wrapper(
    #     agent="SIFT_AGENT_TEST_V6",
    #     agentType=AgentType.SIFT,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_SIFT_L3_T1_6b",
    #     suffix="_062611",
    #     tournament_directory="../tournaments/old/pogo_lvl3b/",
    # )

    # launch_tournament_wrapper(
    #     agent="TUFTS_AGENT_TEST_V3",
    #     agentType=AgentType.TUFTS,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_TUFTS_L2_T7",
    #     suffix="_062522",
    #     tournament_directory="../tournaments/pogo_l2_t7/",
    # )

    # launch_tournament_wrapper(
    #     "TUFTS_AGENT_TEST_V3",
    #     AgentType.TUFTS,
    #     TestType.STAGE5,
    #     global_config,
    #     pool="POGO_TUFTS_X100_1a",
    #     suffix="_062423",
    #     tournament_directory="../tournaments/pogo_lvl1a/",
    # )

    # global_config.set('DEFAULT', 'poolvmcount', '12')

    # launch_tournament_wrapper(
    #     "TUFTS_AGENT_TEST_V3",
    #     AgentType.TUFTS,
    #     TestType.STAGE5,
    #     global_config,
    #     pool="POGO_TUFTS_X100_3a",
    #     suffix="_062423",
    #     tournament_directory="../tournaments/pogo_lvl3a/",
    # )
    #
    # launch_tournament_wrapper(
    #     "TUFTS_AGENT_TEST_V3",
    #     AgentType.TUFTS,
    #     TestType.STAGE5,
    #     global_config,
    #     pool="POGO_TUFTS_X100_3b",
    #     suffix="_062423",
    #     tournament_directory="../tournaments/pogo_lvl3b/",
    # )
    #
    # global_config.set('DEFAULT', 'poolvmcount', '18')
    #
    # launch_tournament_wrapper(
    #     "TUFTS_AGENT_TEST_V3",
    #     AgentType.TUFTS,
    #     TestType.STAGE5,
    #     global_config,
    #     pool="POGO_TUFTS_X100_1b",
    #     suffix="_062423",
    #     tournament_directory="../tournaments/pogo_lvl1b/",
    # )
    # #
    # launch_tournament_wrapper(
    #     "TUFTS_AGENT_TEST_V3",
    #     AgentType.TUFTS,
    #     TestType.STAGE5,
    #     global_config,
    #     pool="POGO_TUFTS_X100_2a",
    #     suffix="_062423",
    #     tournament_directory="../tournaments/pogo_lvl2a/",
    # )
    #
    # launch_tournament_wrapper(
    #     "TUFTS_AGENT_TEST_V3",
    #     AgentType.TUFTS,
    #     TestType.STAGE5,
    #     global_config,
    #     pool="POGO_TUFTS_X100_2b",
    #     suffix="_062423",
    #     tournament_directory="../tournaments/pogo_lvl2b/",
    # )

    # launch_tournament_wrapper(
    #     agent="SRI_AGENT_TEST_V2",
    #     agentType=AgentType.SRI,
    #     test_type=TestType.STAGE6,
    #     global_config=global_config,
    #     pool="HUGA_SRI_VIRGIN_1000",
    #     suffix="_061913",
    #     tournament_directory="../tournaments/all_tournaments_to_TA2/huga/HUGA_L00_T01_S01_VIRGIN/",
    # )


    #
    # launch_tournament_wrapper(
    #     agent="SIFT_AGENT_TEST_V5",
    #     agentType=AgentType.SIFT,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_SIFT_X100_TREES2",
    #     suffix="_061619",
    #     tournament_directory="../tournaments/all_tournaments_to_TA2/pogo/POGO_L02_T01_S01_TREES/",
    #
    # )
    #
    # launch_tournament_wrapper(
    #     agent="SIFT_AGENT_TEST_V5",
    #     agentType=AgentType.SIFT,
    #     test_type=TestType.STAGE5,
    #     global_config=global_config,
    #     pool="POGO_SIFT_X100_AXE2",
    #     suffix="_061619",
    #     tournament_directory="../tournaments/all_tournaments_to_TA2/pogo/POGO_L01_T01_S01_AXE/",
    #
    # )


    # launch_tournament_wrapper( "SIFT_AGENT_TEST_V4",
    #                            AgentType.SIFT,
    #                            TestType.STAGE6,
    #                            global_config,
    #                            pool="POGO_SIFT_X1000_VIRGIN",
    #                            suffix="_061114",
    #                            tournament_directory="../tournaments/all_tournaments_to_TA2/pogo/POGO_L00_T01_S01_VIRGIN/",
    #                         )
    #

    #
    # launch_tournament_wrapper("TUFTS_AGENT_TEST_02",
    #                           AgentType.TUFTS,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="POGO_TUFTS_X100_EMH",
    #                           suffix="_061001",
    #                           tournament_directory="../tournaments/EMH_pogo_provided/",
    #                           )
    # launch_tournament_wrapper("GT_AGENT_2_TEST_V3",
    #                           AgentType.GT_POGO_BASELINE,
    #                           TestType.STAGE5,
    #                           global_config,
    #                           pool="POGO_GT_L2_X100_POOL",
    #                           suffix="_060911",
    #                           tournament_directory="../tournaments/g10/pogo/",
    #                           )

    # launch_tournament_wrapper( "GT_Trained_HUGA_1_V1",
    #                            AgentType.GT_HG_BASELINE,
    #                            TestType.STAGE5,
    #                            global_config,
    #                            pool="HUGA_X100_POOL_GT",
    #                            suffix="_060821",
    #                            tournament_directory="../tournaments/g10/HUGA_L00_T01_S01_VIRGIN/",
    #                         )


