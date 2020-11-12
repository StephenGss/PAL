from enum import Enum


class AgentType(Enum):
    DEFAULT_HG = 0
    SIFT = 1
    TUFTS = 2
    SRI = 3
    GT_HG_BASELINE = 4
    GT_POGO_BASELINE = 5
    GT_HG_BASELINE_MATLAB = 6
    GT_POGO_PLAN_BASELINE = 7
    RAYTHEON = 8
    CRA = 9

class AgentBatchCommands:

    def __init__(self, APP_DICT, agent_name, agent_type=AgentType.DEFAULT_HG):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.application_dict = APP_DICT
        self.git_branch = "dev_unix_sri"  # FIXME: update this as needed
        # self.git_branch = "dev_unix_lockfiles"  # FIXME: update this as needed

    def get_task_commands(self, tournament_zip, tournament_name, suffix=None):

        if self.agent_type == AgentType.SIFT:
            return self._get_sift_agent_commands(tournament_zip, tournament_name, suffix)
        elif self.agent_type == AgentType.TUFTS:
            return self._get_tufts_agent_commands(tournament_zip, tournament_name, suffix)
        elif self.agent_type == AgentType.SRI:
            return self._get_sri_agent_commands(tournament_zip, tournament_name, suffix)
        elif self.agent_type == AgentType.GT_POGO_BASELINE:
            return self._get_gt_pogo_agent_commands(tournament_zip, tournament_name, suffix)
        elif self.agent_type == AgentType.GT_HG_BASELINE:
            return self._get_gt_huga_1_agent_commands(tournament_zip, tournament_name, suffix)
        elif self.agent_type == AgentType.GT_HG_BASELINE_MATLAB:
            return self._get_gt_huga_2_agent_commands(tournament_zip, tournament_name, suffix)
        elif self.agent_type == AgentType.GT_POGO_PLAN_BASELINE:
            return self._get_gt_pogo_plan_agent_commands(tournament_zip, tournament_name, suffix)
        elif self.agent_type == AgentType.RAYTHEON:
            return self._get_raytheon_agent_commands(tournament_zip, tournament_name, suffix)
        elif self.agent_type == AgentType.CRA:
            return self._get_cra_agent_commands(tournament_zip, tournament_name, suffix)
        # TODO: implement additional agent-specific commands here
        else:
            return self._get_default_agent_commands(tournament_zip, tournament_name, suffix)

    def _get_sri_agent_commands(self, tzip, tname, suffix=None):

        if suffix is None:
            suffix = ""

        setup = self._setup_vm()

        github = self._get_github_commands()

        agent_folder_name = 'sri-m12-v1'

        copy_files = [
            'cd $HOME',
            'cp secret_real.ini polycraft/pal/',
            f'if unzip -l {tzip} | grep -q "*/"; then unzip {tzip}; else unzip {tzip} -d {tname}/;fi',
            # f'unzip -l {tzip} | grep -q "*/"',
            # f'if [ "$?" == "0"]; then unzip {tzip}; else unzip {tzip} -d {tname}/; fi',
            # f'unzip {tzip}',
            f'mv {tname}/ polycraft/pal/',
            'echo "[DN_MSG]files copied into pal\n"',
            # 'cp setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
        ]

        copy_agent = [
            'cd $HOME/polycraft/pal',
            'mkdir agents/',
            'cp -r ' + self.application_dict['agent_sri'] + '/* ./agents/',
            'echo "[DN_MSG]agent moved into place\n"',
            f'cd $HOME/polycraft/pal/agents/{agent_folder_name}/',
            'chmod +x *.sh',
            './build.sh',
            f'mv $HOME/setup/sri_run.sh $HOME/polycraft/pal/agents/{agent_folder_name}/',
            'echo "[DN_MSG]SRI Agent Docker Built\n"',
        ]

        launch_polycraft = [
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            'export _JAVA_OPTIONS="-Xmx3G"',
            'export AIGYM_REPORTING=true',
            'export REPORT_SCREEN=true',
            # f'python LaunchTournament.py -t "{suffix}{tname}" -g "../{tname}" -a "{self.agent_name}" -d "../agents/" -x "./play.sh" ',
            f'python LaunchTournament.py -c 1000 -t "{tname}{suffix}" -g "../{tname}" -a "{self.agent_name}" -d "../agents/{agent_folder_name}/" -x "./sri_run.sh" ',
        ]

        return setup + github + copy_files + copy_agent + launch_polycraft

    def _get_tufts_agent_commands(self, tzip, tname, suffix=None):

        if suffix is None:
            suffix=""

        setup = self._setup_vm()

        github = self._get_github_commands()

        copy_files = [
            'cd $HOME',
            'cp secret_real.ini polycraft/pal/',
            f'if unzip -l {tzip} | grep -q "*/"; then unzip {tzip}; else unzip {tzip} -d {tname}/;fi',
            # f'unzip -l {tzip} | grep -q "*/"',
            # f'if [ "$?" == "0"]; then unzip {tzip}; else unzip {tzip} -d {tname}/; fi',
            # f'unzip {tzip}',
            f'mv {tname}/ polycraft/pal/',
            'echo "[DN_MSG]files copied into pal\n"',
            # 'cp setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
            # 'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
        ]

        copy_agent = [
            'cd $HOME/polycraft/pal',
            'mkdir agents/',
            'cp -r ' + self.application_dict['agent_tufts'] + '/v2.0/* ./agents/',
            'echo "[DN_MSG]agent moved into place\n"',
            'docker kill $(docker ps -q) || true',
            'echo "[DN_MSG]attempted to kill running dockers\n"',

        ]

        launch_polycraft = [
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            'export _JAVA_OPTIONS="-Xmx3G"',
            # f'python LaunchTournament.py -t "{suffix}{tname}" -g "../{tname}" -a "{self.agent_name}" -d "../agents/" -x "./play.sh" ',
            f'python LaunchTournament.py -c 1000 -t "{tname}{suffix}" -g "../{tname}" -a "{self.agent_name}" -d "../agents/" -x "./play.sh" -i 600 ',
        ]
        return setup + github + copy_files + copy_agent + launch_polycraft

    def _get_github_commands(self):
        return [
            'cd $HOME',
            'mkdir polycraft && cd polycraft',
            f'git clone -b {self.git_branch} --single-branch https://github.com/StephenGss/pal.git',
            'cd pal/',
            'python -m pip install -U pip',
            'python -m pip install -r requirements.txt --no-cache-dir',
            'cd $HOME',
        ]

    def _setup_vm(self):
        return [
            'dpkg --configure -a',
            'echo "[DN_MSG]dpkg configure re-run\n"',
            './setup/setup_azure_batch_initial.sh',
            'echo "[DN_MSG]azure vm setup complete\n"',
        ]


    def _get_sift_agent_commands(self, tzip, tname, suffix=None):

        if suffix is None:
            suffix=""

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
            'cp -r ' + self.application_dict['agent_sift'] + '/* ./agents/',
            # 'mkdir ./agents/SIFT_SVN/',
            # 'mv ./agents/SIFT\ 2020\ 06\ 16\ 1707/trunk/* ./agents/SIFT_SVN/',
            # 'mv ./agents/SIFT\ \(copy\)/trunk/* ./agents/SIFT_SVN/',
            'echo "[DN_MSG]agent moved into place\n"',
        ]

        copy_files = [
            'cd $HOME',
            'cp secret_real.ini polycraft/pal/',
            f'if unzip -l {tzip} | grep -q "*/"; then unzip {tzip}; else unzip {tzip} -d {tname}/;fi',
            # f'unzip -l {tzip} | grep -q "*/"',
            # f'if [ "$?" == "0"]; then unzip {tzip}; else unzip {tzip} -d {tname}/; fi',
            # f'unzip {tzip}',
            f'mv {tname}/ polycraft/pal/',
            'cp setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/code/test/',
            # 'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
        ]

        build_agent = [
            'cd $HOME/polycraft/pal/agents/code/docker',
            'DOCKER_TAG="latest"; export DOCKER_TAG',
            './build.sh',
            'echo "[DN_MSG]docker build completed\n"',
             '../tools/kill-my-dockers',
            'echo "[DN_MSG]dockers killed\n"',
        ]


        LOG_FILE_DIR = f"/mnt/PolycraftFileShare/sift-12M/{tname}{suffix}/"
        # LOG_FILE_DIR = "$HOME/polycraft/pal/agents/agent_logs_sift/"

        polycraft_launch_cmd = f"./sift_tournament_agent_launcher.sh {LOG_FILE_DIR}"

        launch_polycraft = [
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            # 'sudo pkill Xvfb',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            'export _JAVA_OPTIONS="-Xmx3G"',
            f'python LaunchTournament.py -c 1000 -t "{tname}{suffix}" -g "../{tname}" -a "{self.agent_name}" -d "../agents/code/test/" -x "{polycraft_launch_cmd}"',
        ]

        return start + setup_vm + pull_github + move_agent + copy_files + build_agent + launch_polycraft


    def _get_default_agent_commands(self, tzip, tname, suffix=None):
        return []

    def _get_gt_huga_1_agent_commands(self, tzip, tname, suffix):
        if suffix is None:
            suffix = ""

        setup = self._setup_vm()

        github = self._get_github_commands()

        copy_files = [
            'cd $HOME',
            'cp secret_real.ini polycraft/pal/',
            f'if unzip -l {tzip} | grep -q "*/"; then unzip {tzip}; else unzip {tzip} -d {tname}/;fi',
            # f'unzip -l {tzip} | grep -q "*/"',
            # f'if [ "$?" == "0"]; then unzip {tzip}; else unzip {tzip} -d {tname}/; fi',
            # f'unzip {tzip}',
            f'mv {tname}/ polycraft/pal/',
            'echo "[DN_MSG]files copied into pal\n"',
            # 'cp setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
            # 'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
        ]

        copy_agent = [
            'cd $HOME/polycraft/pal',
            'mkdir agents/',
            'cp -r ' + self.application_dict['agent_gt_huga_1'] + '/* ./agents/',
            'echo "[DN_MSG]agent moved into place\n"',
        ]

        polycraft_launch_cmd = "python Hunter_Gatherer_agent_3_vDN_EDITS.py"

        agent_directory = "../agents/HG_sent_20200606/"

        launch_polycraft = [
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            'export _JAVA_OPTIONS="-Xmx3G"',
            f'python LaunchTournament.py -c 1000 -t "{tname}{suffix}" -g "../{tname}" -a "{self.agent_name}" -d "{agent_directory}" -x "{polycraft_launch_cmd}"',
        ]

        return setup + github + copy_files + copy_agent + launch_polycraft

    def _get_gt_pogo_plan_agent_commands(self, tzip, tname, suffix):
        if suffix is None:
            suffix = ""

        setup = self._setup_vm()

        github = self._get_github_commands()

        copy_files = [
            'cd $HOME',
            'cp secret_real.ini polycraft/pal/',
            f'if unzip -l {tzip} | grep -q "*/"; then unzip {tzip}; else unzip {tzip} -d {tname}/;fi',
            # f'unzip -l {tzip} | grep -q "*/"',
            # f'if [ "$?" == "0"]; then unzip {tzip}; else unzip {tzip} -d {tname}/; fi',
            # f'unzip {tzip}',
            f'mv {tname}/ polycraft/pal/',
            'echo "[DN_MSG]files copied into pal\n"',
            # 'cp setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
            # 'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
        ]

        copy_agent = [
            'cd $HOME/polycraft/pal',
            'mkdir agents/',
            'cp -r ' + self.application_dict['agent_gt_pogo_planner'] + '/* ./agents/',
            'echo "[DN_MSG]agent moved into place\n"',
        ]

        polycraft_launch_cmd = "python 1_python_miner_PLANNER_FF_1_vDN_EDITS.py"

        agent_directory = "../agents/pogo_stick_planner_agent/"

        launch_polycraft = [
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            'export _JAVA_OPTIONS="-Xmx3G"',
            f'python LaunchTournament.py -c 1000 -t "{tname}{suffix}" -g "../{tname}" -a "{self.agent_name}" -d "{agent_directory}" -x "{polycraft_launch_cmd}"',
        ]

        return setup + github + copy_files + copy_agent + launch_polycraft


    def _get_gt_pogo_agent_commands(self, tzip, tname, suffix):

        if suffix is None:
            suffix = ""

        setup = self._setup_vm()

        github = self._get_github_commands()

        copy_files = [
            'cd $HOME',
            'cp secret_real.ini polycraft/pal/',
            f'if unzip -l {tzip} | grep -q "*/"; then unzip {tzip}; else unzip {tzip} -d {tname}/;fi',
            # f'unzip -l {tzip} | grep -q "*/"',
            # f'if [ "$?" == "0"]; then unzip {tzip}; else unzip {tzip} -d {tname}/; fi',
            # f'unzip {tzip}',
            f'mv {tname}/ polycraft/pal/',
            'echo "[DN_MSG]files copied into pal\n"',
            # 'cp setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
            # 'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
        ]

        copy_agent = [
            'cd $HOME/polycraft/pal',
            'mkdir agents/',
            'cp -r ' + self.application_dict['agent_gt_pogo'] + '/* ./agents/',
            'echo "[DN_MSG]agent moved into place\n"',
        ]

        polycraft_launch_cmd = "python 1_python_miner_RL_8_trained_DN.py"

        agent_directory = "../agents/pogo_agent_SENSE_RECIPES/trained_pogo_agent_2/"

        launch_polycraft = [
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            'export _JAVA_OPTIONS="-Xmx3G"',
            f'python LaunchTournament.py -c 1000 -t "{tname}{suffix}" -g "../{tname}" -a "{self.agent_name}" -d "{agent_directory}" -x "{polycraft_launch_cmd}"',
        ]

        return setup + github + copy_files + copy_agent + launch_polycraft

    def _get_gt_huga_2_agent_commands(self, tzip, tname, suffix):
        if suffix is None:
            suffix = ""

        setup = self._setup_vm()

        github = self._get_github_commands()

        copy_files = [
            'cd $HOME',
            'cp secret_real.ini polycraft/pal/',
            f'if unzip -l {tzip} | grep -q "*/"; then unzip {tzip}; else unzip {tzip} -d {tname}/;fi',
            # f'unzip -l {tzip} | grep -q "*/"',
            # f'if [ "$?" == "0"]; then unzip {tzip}; else unzip {tzip} -d {tname}/; fi',
            # f'unzip {tzip}',
            f'mv {tname}/ polycraft/pal/',
            'echo "[DN_MSG]files copied into pal\n"',
            # 'cp setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
            # 'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
        ]

        copy_agent = [
            'cd $HOME/polycraft/pal',
            'mkdir agents/',
            'cp -r ' + self.application_dict['agent_gt_huga_matlab'] + '/* ./agents/',
            'echo "[DN_MSG]agent moved into place\n"',
            'export LD_LIBRARY_PATH=/usr/local/MATLAB/MATLAB_Runtime/v98/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v98/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v98/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v98/extern/bin/glnxa64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}',
        ]

        agent_directory = "../agents/GTech_HG_MATLAB_Agent/"

        polycraft_launch_cmd = "./run_step_04_RL_DQN_simple_try_05_test_online_vDN_EDITS.sh /usr/local/MATLAB/MATLAB_Runtime/v98"

        launch_polycraft = [
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            'export _JAVA_OPTIONS="-Xmx3G"',
            f'python LaunchTournament.py -c 1000 -t "{tname}{suffix}" -g "../{tname}" -a "{self.agent_name}" -d "{agent_directory}" -x "{polycraft_launch_cmd}"',
        ]

        return setup + github + copy_files + copy_agent + launch_polycraft

    def _get_raytheon_agent_commands(self, tzip, tname, suffix):

        if suffix is None:
            suffix = ""

        setup = self._setup_vm()

        github = self._get_github_commands()

        copy_files = [
            'cd $HOME',
            'cp secret_real.ini polycraft/pal/',
            # f'unzip -l {tzip} | grep -q "*/"',
            f'if unzip -l {tzip} | grep -q "*/"; then unzip {tzip}; else unzip {tzip} -d {tname}/;fi',
            # f'if [ "$?" == "0"]; then unzip {tzip}; else unzip {tzip} -d {tname}/; fi',
            # f'unzip {tzip}',
            f'mv {tname}/ polycraft/pal/',
            'echo "[DN_MSG]files copied into pal\n"',
            # 'cp setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
            # 'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
        ]

        copy_agent = [
            'cd $HOME/polycraft/pal',
            'mkdir agents/',
            'cp -r ' + self.application_dict['agent_raytheon'] + '/* ./agents/',
            f'cd agents/',
            'find . -not -type d -exec file "{}" ";" | grep CRLF | sed -n "s/:.*//p" | xargs -I {} sed -i "s/\r$//g" {}',
            'echo "[DN_MSG]CRLF endings removed"',
            'echo "[DN_MSG]attempting to insert: \\n\\        \\\'$HOME/polycraft/pal/agents/Huga/ImageProcessing/checkpoint.pth.tar\\\' into fast.py"',
            "sed -i -e \"s+\\'paths\\' : \[+&\\n\\        '$HOME/polycraft/pal/agents/Huga/ImageProcessing/checkpoint.pth.tar',+\" Huga/ImageProcessing/fast.py",
            'echo "[DN_MSG]agent moved into place\n"',
        ]

        agent_directory = "../agents/"

        polycraft_launch_cmd = "python -m Huga.TournamentAgent"

        launch_polycraft = [
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            'export _JAVA_OPTIONS="-Xmx3G"',
            f'python LaunchTournament.py -c 1000 -t "{tname}{suffix}" -g "../{tname}" -a "{self.agent_name}" -d "{agent_directory}" -x "{polycraft_launch_cmd}"',
        ]

        # return github + copy_files + copy_agent

        # return setup + github + copy_files + copy_agent
        return setup + github + copy_files + copy_agent + launch_polycraft

    def _get_cra_agent_commands(self, tzip, tname, suffix):
        if suffix is None:
            suffix = ""

        setup = self._setup_vm()

        github = self._get_github_commands()

        copy_files = [
            'cd $HOME',
            'cp secret_real.ini polycraft/pal/',
            # f'unzip -l {tzip} | grep -q "*/"',
            f'if unzip -l {tzip} | grep -q "*/"; then unzip {tzip}; else unzip {tzip} -d {tname}/;fi',
            # f'if [ "$?" == "0"]; then unzip {tzip}; else unzip {tzip} -d {tname}/; fi',
            # f'unzip {tzip}',
            f'mv {tname}/ polycraft/pal/',
            'echo "[DN_MSG]files copied into pal\n"',
            # 'cp setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
            # 'mv setup/sift_tournament_agent_launcher.sh polycraft/pal/agents/SIFT_SVN/code/test/',
        ]

        copy_agent = [
            'cd $HOME/polycraft/pal',
            'mkdir agents/',
            'wget https://julialang-s3.julialang.org/bin/linux/x64/1.3/julia-1.3.1-linux-x86_64.tar.gz',
            'tar -xf julia-1.3.1-linux-x86_64.tar.gz',

            'sudo ln -s $(pwd)/julia-1.3.1/bin/julia /usr/local/bin/julia',

            'cp -r ' + self.application_dict['agent_cra'] + '/* ./agents/',
            f'cd agents/',
            'julia setup.jl',
            # 'find . -not -type d -exec file "{}" ";" | grep CRLF | sed -n "s/:.*//p" | xargs -I {} sed -i "s/\r$//g" {}',
            # 'echo "[DN_MSG]CRLF endings removed"',
            # 'echo "[DN_MSG]attempting to insert: \\n\\        \\\'$HOME/polycraft/pal/agents/Huga/ImageProcessing/checkpoint.pth.tar\\\' into fast.py"',
            # "sed -i -e \"s+\\'paths\\' : \[+&\\n\\        '$HOME/polycraft/pal/agents/Huga/ImageProcessing/checkpoint.pth.tar',+\" Huga/ImageProcessing/fast.py",
            'echo "[DN_MSG]agent moved into place\n"',
        ]

        agent_directory = "../agents/"

        polycraft_launch_cmd = "julia deploy.jl"

        launch_polycraft = [
            'cd $HOME/polycraft/pal/PolycraftAIGym',
            'mkdir Logs',
            'echo "[DN_MSG]hopefully moved into the right folder?\n"',
            'export _JAVA_OPTIONS="-Xmx3G"',
            f'python LaunchTournament.py -c 1000 -t "{tname}{suffix}" -g "../{tname}" -a "{self.agent_name}" -d "{agent_directory}" -x "{polycraft_launch_cmd}"',
        ]

        # return github + copy_files + copy_agent

        # return setup + github + copy_files + copy_agent
        return setup + github + copy_files + copy_agent + launch_polycraft



if __name__ == '__main__':
    temp_dict = {
        'agent_sift': 'TEST_SIFT',
        'agent_tufts': "TEST_TUFTS"
    }
    var = AgentBatchCommands(temp_dict, "sift_test", AgentType.SIFT)
    a = var.get_task_commands("test.zip", "test")
