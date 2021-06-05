import numpy as np
from PolycraftAIGym.AzureConnectionService import AzureConnectionService
from PolycraftAIGym.PalMessenger import PalMessenger
import pandas as pd
import json
import os
import matplotlib.pyplot as plt
import random
from sklearn.metrics import auc
from collections import defaultdict, OrderedDict
from pathlib import Path
from datetime import datetime


class AMOC_Calculations:

    def __init__(self, title, in_file=None, agent_name='SIFT_AGENT_TEST_V6', tournament_likeness='062611',debug=False, outfile=None, **kwargs):
        self.title = title
        self.debug = debug
        self.in_file = in_file
        self.F = 0
        self.S = 0
        self.R = list()
        # self.level_dict = DefaultOrderedDict(lambda: DefaultOrderedDict(lambda: DefaultOrderedDict(lambda: DefaultOrderedDict(lambda: dict()))))
        self.level_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: dict()))))
        self.granular_auc = []
        self.output_dir = Path(f"C:\\Users\\{os.getlogin()}\\Polycraft World\\Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\000. Evaluations\\00. Raw Data for DARPA formatting\\01. AMOC\\{self.title}\\")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # If KWARGS is not none, update the variables:
        for key in ('in_file', 'agent_name', 'tournament_likeness', 'debug'):
            if key in kwargs:
                setattr(self, key, kwargs[key])

        self.outfile = outfile
        if outfile is None:
            self.outfile = "temp.csv"
        if self.in_file is not None:
            self.read_original_input_file()
        else:
            self.data = self.load_tournament_metrics(agent_name, tournament_likeness)
            # self.data.to_csv(f"{outfile}.csv")
            self.read_polycraft_data()

    def load_tournament_metrics(self, agent_name, tournament_likeness) -> pd.DataFrame:
        """
        DATA ACCESSOR FUNCTION.
        Runs a hard-coded sql statement (varying the WHERE filter with Agent_name and tournament_likeness)
        to get necessary data for AMOC

        All tables and columms are hard-coded and may need changing.
        """
        # a = f"SELECT * FROM {agent_name}_Results_View where Tournament_Name like '%{tournament_likeness}%'"
        if self.debug:
            # a = f"SELECT tournament_name, game_novelty_starts, coalesce(game_novelty_detected, -1) from TOURNAMENT_METRICS_VIEW WHERE Agent_Name = '{agent_name}' and Tournament_Name like '%{tournament_likeness}%'"
            a = f"""SELECT TOURNAMENT_NAME, 
                    NOVELTY_IDENTIFIER, 
                    DIFFICULTY, 
                    TOURNAMENT_DIFF_TYPE, 
                    TOURNAMENT_VARIANT, 
                    GAME_NOVELTY_STARTS, 
                    coalesce(game_novelty_detected, -1) AS GAME_NOVELTY_DETECTED, 
                    COUNT_GAMES_PLAYED 
                from TOURNAMENT_METRICS_VIEW 
                WHERE Agent_Name = '{agent_name}' 
                and Tournament_Name like '%{tournament_likeness}%' 
                and TOURNAMENT_DIFF_TYPE <> 'A'
                and TOURNAMENT_NAME not like 'POGO_L02_T01_S02_TREES_X0100_H_U0016_V2_062611'"""
            # a = f"SELECT TOP (10000) A.*, ZONE.* FROM {agent_name}_Results_View A LEFT JOIN LOOKUP_PERFORMANCE_ZONES ZONE on Zone.Agent_Name = '{agent_name}' and A.Tournament_Name like '%' + Zone.Tournament_Name + '%' where A.Tournament_Name like '%{tournament_likeness}%'"
        else:
            #from TOURNAMENT_METRICS_VIEW
            a = f"""SELECT      NOVELTY_LEVEL,
                                TOURNAMENT_DIFF_TYPE, 
                                NOVELTY_IDENTIFIER, 
                                'N/A' as DIFFICULTY,
                                TOURNAMENT_VARIANT, 
                                MIN(GAME_NOVELTY_STARTS) AS GAME_NOVELTY_STARTS, 
                                MIN(coalesce(game_novelty_detected, -1)) AS GAME_NOVELTY_DETECTED, 
                                MIN(COUNT_GAMES_PLAYED) AS COUNT_GAMES_PLAYED 
                            from TOURNAMENT_METRICS_12M_TABLE_V1 
                            WHERE Agent_Name = '{agent_name}' 
                            and Tournament_Name like '%{tournament_likeness}%' 
                            and TOURNAMENT_NAME not like 'POGO_L02_T01_S02_TREES_X0100_H_U0016_V2_062611'
                            and TOURNAMENT_NAME not like '%VIRGIN%'
                    GROUP BY NOVELTY_LEVEL, TOURNAMENT_DIFF_TYPE, NOVELTY_IDENTIFIER, TOURNAMENT_VARIANT
                    """

            # a = f"SELECT tournament_name, NOVELTY_IDENTIFIER, DIFFICULTY, TOURNAMENT_DIFF_TYPE, TOURNAMENT_VARIANT, game_novelty_starts, coalesce(game_novelty_detected, -1) from TOURNAMENT_METRICS_VIEW WHERE Agent_Name = '{agent_name}' and Tournament_Name like '%{tournament_likeness}%'"
            # a = f"SELECT A.*, ZONE.* FROM {agent_name}_Results_View A LEFT JOIN LOOKUP_PERFORMANCE_ZONES ZONE on Zone.Agent_Name = '{agent_name}' and A.Tournament_Name like '%' + Zone.Tournament_Name + '%' where A.Tournament_Name like '%{tournament_likeness}%'"

        ## Connect to the SQL database and run the above statements.
        pm = PalMessenger(True, False)
        azure = AzureConnectionService(pm)
        if azure.is_connected():
            return pd.read_sql(a, azure.sql_connection)

    def read_polycraft_data(self):
        for key, row in self.data.iterrows():
            # game_id_loc = obj["game_id"]
            # sep_parts = game_id_loc.split("-")
            level = row['NOVELTY_LEVEL']

            # novelty_level = sep_parts[1] + '-' + sep_parts[2]
            # diff_level = row['DIFFICULTY']
            # diff_level = sep_parts[3]
            difficulty = row['TOURNAMENT_DIFF_TYPE']
            novelty_level = row['NOVELTY_IDENTIFIER']
            # distribution = sep_parts[5] + '-' + sep_parts[6]
            tournament_num = row['TOURNAMENT_VARIANT']
            # tournament_num = sep_parts[7] + '-' + sep_parts[8]
            self.level_dict[level][difficulty][novelty_level][tournament_num]['actual_novelty_index'] = min(
                int(row['GAME_NOVELTY_STARTS']), int(row['COUNT_GAMES_PLAYED']))
            self.level_dict[level][difficulty][novelty_level][tournament_num]['output_novelty_index'] = int(
                row['GAME_NOVELTY_DETECTED'])
            self.level_dict[level][difficulty][novelty_level][tournament_num]['games_in_tournament'] = int(
                row['COUNT_GAMES_PLAYED'])
            # self.level_dict[level][difficulty][novelty_level][tournament_num]['auc'] = 0
            self.level_dict[level][difficulty][novelty_level][tournament_num][
                'output_novelty_index_random'] = random.randint(1, int(row['COUNT_GAMES_PLAYED']))

    def read_original_input_file(self):
        count = 0
        with open(self.in_file, 'r') as f:
            for line in f:
                obj = json.loads(line[0:-1])
                game_id_loc = obj["game_id"]
                sep_parts = game_id_loc.split("-")
                novelty_level = sep_parts[1] + '-' + sep_parts[2]
                diff_level = sep_parts[3]
                distribution = sep_parts[5] + '-' + sep_parts[6]
                tournament_num = sep_parts[7] + '-' + sep_parts[8]
                self.level_dict[novelty_level][diff_level][distribution][tournament_num]['actual_novelty_index'] = int(obj['Actual novelty game index'])
                self.level_dict[novelty_level][diff_level][distribution][tournament_num]['output_novelty_index'] = int(obj['Output novelty game index'])
                self.level_dict[novelty_level][diff_level][distribution][tournament_num]['output_novelty_index_random'] = random.randint(1, 20)
                self.level_dict[novelty_level][diff_level][distribution][tournament_num]['games_in_tournament'] = 20

    def calculate_by_tournament(self):
        """
        PERFORM AMOC CALCULATIONS PER TOURNAMENT - methodology from Mayank Kejriwal's team.
        """
        self.F = 0
        self.S = 0
        self.R = list()
        F = 0
        S = 0
        R = list()
        count = 0

        for lvl in self.level_dict.keys():
            print(f"lvl: {lvl}")
            for diff in self.level_dict[lvl].keys():
                print(f"diff: {diff}")
                for d in self.level_dict[lvl][diff].keys():
                    print(f"d: {d}")
                    # F = 0
                    # S = 0
                    # R = list()
                    for k in self.level_dict[lvl][diff][d].keys():
                        F = 0
                        S = 0
                        R = list()
                        print(f"k: {k}")
                        count += 1

                        actual_ind = self.level_dict[lvl][diff][d][k]['actual_novelty_index']
                        detected_ind = self.level_dict[lvl][diff][d][k]['output_novelty_index']
                        instances = self.level_dict[lvl][diff][d][k]['games_in_tournament']
                        # Iterate through all played games in the tournament and apply the appropriate penalty for the earliest FP
                        # ASSUMPTION:
                        #   - Agent is expected to report novelty ONLY ONCE per tournament and the earliest report
                        #   - is counted for it
                        #   - TODO: if agents improve their detection/reporting, then we need to revise AMOC calculation
                        for game_id in range(0, instances):
                            if actual_ind is None or detected_ind is None:
                                continue
                            if detected_ind == -1 or detected_ind < game_id:  # no detection
                                self.R.append([self.F, self.S])
                                R.append([F, S])
                            elif detected_ind < actual_ind:  # FP>0 and TP>0
                                for i in range(game_id, actual_ind):
                                    self.F += 1
                                    F += 1
                                    self.R.append([self.F, self.S])
                                    R.append([F, S])
                                self.S += (instances - actual_ind)
                                S += (instances - actual_ind)
                                self.R.append([self.F, self.S])
                                R.append([F, S])
                            elif detected_ind >= actual_ind:  # no FP
                                self.S += (instances - detected_ind)
                                S += (instances - detected_ind)
                                self.R.append([self.F, self.S])
                                R.append([F, S])

                        F_total = F
                        # if F == 0:
                        #     F_total = 1
                        S_total = S
                        # if S==0:
                        #     S_total = 1
                        F_list = list()
                        S_list = list()
                        auc_val = -1
                        if S_total == 0:
                            auc_val = 0
                        elif F_total == 0:
                            auc_val = 1
                        else:
                            for i in range(len(R)):
                                R[i][0] = R[i][0] / F_total
                                F_list.append(R[i][0])
                                R[i][1] = R[i][1] / S_total
                                S_list.append(R[i][1])

                            F_list = sorted(F_list)
                            S_list = sorted(S_list)

                            plt.plot(S_list, F_list)
                            plt.xlabel('False alarm rate')
                            plt.ylabel('Average Score')
                            # try:
                            auc_val = auc(S_list, F_list)
                            # except ValueError:
                            #     auc_val = 1
                            plt.title(f'AMOC {self.title}_{lvl}_{diff}_{k}, AUC = {str(auc_val)}')
                            plt.savefig(self.output_dir / f"AMOC {self.title}_{lvl}_{diff}_{k}.png", format='png')
                            plt.close()
                        self.granular_auc.append({"novelty": lvl, "difficulty": diff, "type": d, "instance": k, "auc": auc_val})
                # self.level_dict[lvl][diff]['auc'] = auc(S_list, F_list)
        self.__save_tournament_to_csv()

    def __save_tournament_to_csv(self):
        """
        Save output dataframe to a csv in the target directory
        """
        df = pd.DataFrame(self.granular_auc)
        df.to_csv(self.output_dir / f"{self.outfile}.csv")

    def create_amoc_plots(self):
        """
        Create AMOC summary graphs
        """
        if self.F == 0:
            self.F = 1
        F_total = self.F
        S_total = self.S
        F_list = list()
        S_list = list()

        for i in range(len(self.R)):
            self.R[i][0] = self.R[i][0]/F_total
            F_list.append(self.R[i][0])
            self.R[i][1] = self.R[i][1]/S_total
            S_list.append(self.R[i][1])

        F_list = sorted(F_list)
        S_list = sorted(S_list)

        plt.close()
        plt.plot(S_list, F_list)
        plt.xlabel('False alarm rate')
        plt.ylabel('Average Score')
        auc_val = auc(S_list, F_list)

        plt.title(f'AMOC {self.title}, AUC = {str(auc_val)}')
        # plt.show()
        # plt.savefig("AMOC")
        plt.savefig(self.output_dir / f"AMOC {self.title} Final.png", format='png')
        print(auc_val)

def runAMOC(agentName, tournamentFilter, debug=False):
    """
    Helper function that runs the AMOC calculations for a given script
    """
    amoc = AMOC_Calculations(agentName, agent_name=agentName, tournament_likeness=tournamentFilter,
                             outfile=f'{agentName}_data_{datetime.strftime(datetime.today(),"%Y.%m.%d_%H%M")}', debug=debug)
    amoc.calculate_by_tournament()
    amoc.create_amoc_plots()


if __name__ == '__main__':

    # NOTE: If you ran a U and K tournament on the same tournament Date, then you can input: "U%052701" or "K%052701"
    # to the tournamentFilter to down-filter to the right subset of tournaments to run AMOC for.

    # All Outputs are saved to:
    # Polycraft World (Internal) - Documents\\05. SAIL-ON Program\\000. Evaluations\\00. Raw Data for DARPA formatting\\01. AMOC\\{agentName}\\

    # Example below - please rename/comment/reuse
    runAMOC(agentName="GTECH_18M_E2", tournamentFilter="052701")


