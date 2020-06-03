import unittest
from AzureBatch.AgentBatchCommands import AgentBatchCommands, AgentType
# from AzureBatch.AzureBatchLaunchTournaments import AgentType

class MyTestCase(unittest.TestCase):

    def test_tufts_agent(self):
        tzip = 'test.zip'
        tname = 'test'
        self.git_branch = 'dev_unix_sri'
        self.application_dict = {
            'agent_sift': 'TEST_SIFT',
            'agent_tufts': "TEST_TUFTS"
        }
        self.agent_name = "tufts_test"
        var = AgentBatchCommands(self.application_dict, self.agent_name, AgentType.TUFTS)
        a = var.get_task_commands(tzip, tname)
        # APPLICATION_DIR = temp_dict['agent_sift']

        running = [
            'printenv',
            './setup/setup_azure_batch_initial.sh',
            'mkdir polycraft && cd polycraft',
            f'git clone -b {self.git_branch} --single-branch https://github.com/StephenGss/pal.git',
            'cd pal/',
            'python -m pip install -U pip',
            'python -m pip install -r requirements.txt',
            'cd $HOME',
            'mv secret_real.ini polycraft/pal/',
            f'unzip {tzip} && mv {tname}/ polycraft/pal/',
            'cd $HOME/polycraft/pal',
            'mkdir agents/',
            'mv ' + self.application_dict['agent_tufts'] + '/* ./agents/',
            'echo "[DN_MSG]agent moved into place\n"',
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            f'python LaunchTournament.py -t "BATCH_{tname}" -g "../{tname}" -a "{self.agent_name}" -d "../agents/TUFTS/" -x "./play.sh" ',
        ]

        differences = list(set(running) - set(a))
        print(differences)
        self.assertEqual(len(differences), 0)

    def test_sift_agent(self):
        file = 'test.zip'
        filename = 'test'
        temp_dict = {
            'agent_sift': 'TEST_SIFT',
            'agent_tufts': "TEST_TUFTS"
        }
        var = AgentBatchCommands(temp_dict, "sift_test", AgentType.SIFT)
        a = var.get_task_commands("test.zip", "test")
        APPLICATION_DIR = temp_dict['agent_sift']
        running = [
                'printenv',
                'USER="root"; export USER',
                'printenv',
                'sudo apt-get install zip unzip build-essential -y',
                # 'sudo apt install docker.io -y && sudo systemctl start docker && sudo systemctl enable docker && sudo groupadd docker && sudo usermod -aG docker $USER',
                # 'exec (exec newgrp docker)',
                # 'docker ps',
                # 'echo "worked!"'
                'echo "[DN_MSG]additional pkgs installed\n"',
                # 'mkdir polycraft && mkdir polycraft/pal',  ## Temporary
                './setup/setup_azure_vm.sh', # TODO: Move this to startup script
                # 'sudo ./setup/setup_azure_vm.sh', # TODO: Move this to startup script
                'echo "[DN_MSG]azure vm setup complete\n"',
                # 'mkdir polycraft && cd polycraft',
                # 'git clone -b dev_unix_sri --single-branch https://github.com/StephenGss/pal.git',
                # 'cd pal/',
                # 'python -m pip install -U pip',
                # 'python -m pip install -r requirements.txt',
                # 'cd $HOME',
                f'unzip {file} && mv {filename}/ polycraft/pal/',
                'cd polycraft/pal',
                'mkdir agents/',
                'mv ' + APPLICATION_DIR + '/* ./agents/',
                'mkdir ./agents/SIFT_SVN/',
                'mv ./agents/SIFT\ \(copy\)/trunk/* ./agents/SIFT_SVN/',
                # 'sudo mv ' + APPLICATION_DIR + '/* ./agents/',
                # 'sudo chown -R $USER ./agents/',
                'echo "[DN_MSG]agent moved into place\n"',
                # 'exec sudo su -l $USER',
                'cd ./agents/SIFT_SVN/code/docker',
                'DOCKER_TAG="latest"; export DOCKER_TAG',
                './build.sh',
                'echo "[DN_MSG]docker build completed\n"',
                '../tools/kill-my-dockers',
                'echo "[DN_MSG]dockers killed\n"',
                'cd $HOME',
                'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
                'cd $HOME/polycraft/pal/PolycraftAIGym',
                'mkdir Logs',
                'echo "[DN_MSG]hopefully moved into the right folder?\n"',
                'sudo touch /home/root/.bashrc && sudo chmod 777 /home/root/.bashrc',
                f'python LaunchTournament.py -t "BATCH_{filename}" -g "../{filename}/"',
                # 'printenv',
                # 'sudo -S apt-get install -y python3-opencv',
                # 'sudo pip3 install -r ' + APPLICATION_DIR + '/requirements.txt',
                # 'python3 ' + APPLICATION_DIR + '/sense_screen_image.py'
            ]

        differences = list(set(running) - set(a))
        print(differences)
        self.assertEqual(len(differences), 0)


if __name__ == '__main__':
    unittest.main()
