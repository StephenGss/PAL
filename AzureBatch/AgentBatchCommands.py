from enum import Enum


class AgentType(Enum):
    DEFAULT_HG = 0
    SIFT = 1
    TUFTS = 2
    SRI = 3
    GT_HG_BASELINE = 4
    GT_POGO_BASELINE = 5

class AgentBatchCommands:

    def __init__(self, APP_DICT, agent_name, agent_type=AgentType.DEFAULT_HG):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.application_dict = APP_DICT
        self.git_branch = "dev_unix_sri"  # FIXME: update this as needed

    def get_task_commands(self, tournament_zip, tournament_name):

        if self.agent_type == AgentType.SIFT:
            return self._get_sift_agent_commands(tournament_zip, tournament_name)
        elif self.agent_type == AgentType.TUFTS:
            return self._get_tufts_agent_commands(tournament_zip, tournament_name)
        elif self.agent_type == AgentType.SRI:
            return self._get_sri_agent_commands(tournament_zip, tournament_name)
        # TODO: implement additional agent-specific commands here
        else:
            return self._get_default_agent_commands(tournament_zip, tournament_name)

    def _get_sri_agent_commands(self, tzip, tname):
        return [
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
            'cd polycraft/pal',
            'mkdir agents/',
            'cp -r ' + self.application_dict['agent_tufts'] + '/* ./agents/',
            'echo "[DN_MSG]agent moved into place\n"',
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            f'python LaunchTournament.py -t "BATCH_{tname}" -g "../{tname}" -a "{self.agent_name}" -d "../agents/TUFTS/" -x "./play.sh" ',
        ]


    def _get_tufts_agent_commands(self, tzip, tname):
        return [
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
            'cd polycraft/pal',
            'mkdir agents/',
            'mv ' + self.application_dict['agent_tufts'] + '/* ./agents/',
            'echo "[DN_MSG]agent moved into place\n"',
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            f'python LaunchTournament.py -t "BATCH_{tname}" -g "../{tname}" -a "{self.agent_name}" -d "../agents/TUFTS/" -x "./play.sh" ',
        ]

    def _get_github_commands(self):
        return [
            'cd $HOME',
            'mkdir polycraft && cd polycraft',
            f'git clone -b {self.git_branch} --single-branch https://github.com/StephenGss/pal.git',
            'cd pal/',
            'python -m pip install -U pip',
            'python -m pip install -r requirements.txt',
            'cd $HOME',
        ]

    def _setup_vm(self):
        return [
            './setup/setup_azure_batch_initial.sh',
            'echo "[DN_MSG]azure vm setup complete\n"',
        ]

    def _get_sift_agent_commands(self, tzip, tname):

        start = [
            'printenv',
            # './setup/setup_azure_batch_initial.sh',
            'USER="root"; export USER',
            'printenv',
            'sudo apt-get install zip unzip build-essential -y',
            'echo "[DN_MSG]additional pkgs installed\n"',
        ]

        setup_vm = self._setup_vm()

        pull_github = self._get_github_commands()

        # Use this for App version 4 - packaged by Jim
        move_agent = [
            'cd $HOME/polycraft/pal',
            'mkdir agents/',
            'mv ' + self.application_dict['agent_sift'] + '/* ./agents/',
            'mkdir ./agents/SIFT_SVN/',
            'mv ./agents/SIFT\ \(copy\)/trunk/* ./agents/SIFT_SVN/',
            'echo "[DN_MSG]agent moved into place\n"',
        ]

        copy_files = [
            'cd $HOME',
            'mv secret_real.ini polycraft/pal/',
            f'unzip {tzip} && mv {tname}/ polycraft/pal/',
            'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
            # 'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
        ]

        build_agent = [
            'cd $HOME/polycraft/pal/agents/SIFT_SVN/code/docker',
            'DOCKER_TAG="latest"; export DOCKER_TAG',
            './build.sh',
            'echo "[DN_MSG]docker build completed\n"',
            '../tools/kill-my-dockers',
            'echo "[DN_MSG]dockers killed\n"',
        ]

        LOG_FILE_DIR = "$HOME/polycraft/pal/agents/agent_logs_sift/"

        polycraft_launch_cmd = f"./sift_tournament_agent_launcher.sh {LOG_FILE_DIR}"

        launch_polycraft = [
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            'export _JAVA_OPTIONS="-Xmx3G"',
            f'python LaunchTournament.py -t "BATCH_{tname}" -g "../{tname}" -a "{self.agent_name}" -d "../agents/SIFT_SVN/code/test/" -x "{polycraft_launch_cmd}"',
        ]

        return start + setup_vm + pull_github + move_agent + copy_files + build_agent + launch_polycraft

        # return [
        #     'printenv',
        #     # './setup/setup_azure_batch_initial.sh',
        #     'USER="root"; export USER',
        #     'printenv',
        #     'sudo apt-get install zip unzip build-essential -y',
        #     'echo "[DN_MSG]additional pkgs installed\n"',
        #     './setup/setup_azure_batch_initial.sh',
        #     'echo "[DN_MSG]azure vm setup complete\n"',
        #     'mkdir polycraft && cd polycraft',
        #     f'git clone -b {self.git_branch} --single-branch https://github.com/StephenGss/pal.git',
        #     'cd pal/',
        #     'python -m pip install -U pip',
        #     'python -m pip install -r requirements.txt',
        #     'cd $HOME',
        #     'mv secret_real.ini polycraft/pal/',
        #     f'unzip {tzip} && mv {tname}/ polycraft/pal/',
        #     'cd polycraft/pal',
        #     'mkdir agents/',
        #     'mv ' + self.application_dict['agent_sift'] + '/* ./agents/',
        #     'echo "[DN_MSG]agent moved into place\n"',
        #     'cd ./agents/SIFT_SVN/code/docker',
        #     './build.sh',
        #     'echo "[DN_MSG]docker build completed\n"',
        #     '../tools/kill-my-dockers',
        #     'echo "[DN_MSG]dockers killed\n"',
        #     'cd $HOME/polycraft/pal/PolycraftAIGym',
        #     'mkdir Logs',
        #     'echo "[DN_MSG]hopefully moved into the right folder?\n"',
        #     f'python LaunchTournament.py -t "BATCH_{tname}" -g "../{tname}"',
        # ]




    def _get_default_agent_commands(self, tzip, tname):
        return []


if __name__ == '__main__':
    temp_dict = {
        'agent_sift': 'TEST_SIFT',
        'agent_tufts': "TEST_TUFTS"
    }
    var = AgentBatchCommands(temp_dict, "sift_test", AgentType.SIFT)
    a = var.get_task_commands("test.zip", "test")
