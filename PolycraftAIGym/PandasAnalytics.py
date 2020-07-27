from PolycraftAIGym.AzureConnectionService import AzureConnectionService
from PolycraftAIGym.PalMessenger import PalMessenger
import pandas as pd
import numpy as np
from enum import Enum

debug = False



def stack_baseline(group, baselineA):
    # group.loc[:, 'type'] = 'NOVEL'
    # group = remainder[remainder['Tournament_Name'] ==  'POGO_L01_T01_S01_AXE_X0100_A_U0014_V2_062611']
    original_cols = baselineA.columns.to_list()
    merged_baseline = baselineA.merge(group, on='Game_ID', how='outer', suffixes=('', '_other'))
    # merged_baseline = baselineA.join(group, on='Game_ID', how='left', rsuffix='_other')
    # Adjust Virgin Values
    new_cols = merged_baseline.columns.to_list()
    if 'Difficulty_other' not in new_cols:
        print("Error! Difficulty_other not in the list!")
    merged_baseline['Final_Reward_Old'] = merged_baseline['Final_Reward']

    # merged_baseline['Final_Reward'] = merged_baseline.apply(lambda d:
    #                                                         d['Final_Reward_Old'] if d[
    #                                                                                      'Difficulty_other'] == np.nan else (
    #                                                             d['Final_Reward_Old'] - (d['PreNovelty_Low_other'] - d[
    #                                                                 'Easy_Low_other'])
    #                                                             if d['Difficulty_other'] == "Easy" else (
    #                                                     d['Final_Reward_Old'] - (d['PreNovelty_Low_other'] - d['Medium_Low_other'])
    #                                                                 if d['Difficulty_other'] == "Medium" else (
    #                                                                     d['Final_Reward_Old'] - (
    #                                                                                 d['PreNovelty_Low_other'] - d[
    #                                                                             'Hard_Low_other'])
    #                                                                     if d['Difficulty_other'] == "Hard" else (
    #                                                                         d['Final_Reward_Old'])))), axis=1)

    merged_baseline['Final_Reward'] = merged_baseline.apply(lambda d:
            d['Final_Reward_Old'] if (pd.isnull(d['Difficulty_other']) or pd.isnull(d['PreNovelty_Low_other'])) else (
                d['Final_Reward_Old'] - ((d['PreNovelty_High_other'] + d['PreNovelty_Low_other'])/2.0 - (d['Easy_High_other'] + d['Easy_Low_other'])/2.0)
                    if d['Difficulty_other'] == "Easy" else (
                        d['Final_Reward_Old'] - ((d['PreNovelty_High_other'] + d['PreNovelty_Low_other'])/2.0 - (d['Medium_High_other'] + d['Medium_Low_other'])/2.0)
                        if d['Difficulty_other'] == "Medium" else (
                            d['Final_Reward_Old'] - ((d['PreNovelty_High_other'] + d['PreNovelty_Low_other'])/2.0 - (d['Hard_High_other'] + d['Hard_Low_other'])/2.0)
                            if d['Difficulty_other'] == "Hard" else (
                                d['Final_Reward_Old'])))), axis=1)

    merged_baseline = merged_baseline[original_cols]

    group.insert(0, 'type', 'NOVEL')

    r = pd.concat([group, merged_baseline])
    r['Adjusted_Reward'] = r[['Final_Reward', 'Intermediate_Reward']].values.max(1)
    r['rank'] = r['Adjusted_Reward'].rank(method='average')
    # r.loc[r.type == 'VIRGIN', 'r_sum_base'] = r.rank
    # r.loc[r.type == 'NOVEL', 'r_sum_novel'] = r.rank
    r['r_sum_base'] = r.apply(lambda f: (f['rank']) * np.where(f['type'] == 'VIRGIN', 1, 0), axis=1)
    r['r_sum_novel'] = r.apply(lambda f: (f['rank']) * np.where(f['type'] == 'NOVEL', 1, 0), axis=1)
    # r['Avg_Adjusted'] = r.apply(avg, axis=1)
    grouped = r.groupby('Tournament_Name')

    e = grouped.apply(lambda x: pd.Series(dict(
        avg_base_adjusted_reward=x[x['type'] == 'VIRGIN']['Adjusted_Reward'].sum(),
        avg_novel_adjusted_reward=x[x['type'] == 'NOVEL']['Adjusted_Reward'].sum(),
        # avg_final_reward=x.Adjusted_Reward.sum(),
        R=x['rank'].sum(),
        N=x['rank'].count(),
        V_R1=x.r_sum_base.sum(),
        R1=x.r_sum_novel.sum(),
        V_N1=x[x['type'] == 'VIRGIN']['r_sum_base'].count(),
        N1=x[x['type'] == 'NOVEL']['r_sum_novel'].count(),
    )))
    total = e['N'].product()

    result = pd.DataFrame()

    result.insert(0, 'Tournament_Name', [i for i in e.index if 'VIRGIN' not in i])

    r = []
    for index, row in e.iterrows():
        if 'VIRGIN' in index:
            result.insert(1, 'V_R1', [row['R']])
            result.insert(2, 'V_N1', [row['N']])
            result.insert(3, 'V_U1', [(row['R'] - (row['N'] * (row['N'] + 1)) / 2)])
            result.insert(4, 'Avg_Baseline_Reward', [(row['avg_base_adjusted_reward']) / row['N']])
            continue

        result.insert(5, 'R1', [row['R']])
        result.insert(6, 'N1', [row['N']])
        result.insert(7, 'U1', [(row['R'] - (row['N'] * (row['N'] + 1)) / 2)])
        result.insert(8, 'Avg_Novel_Reward', [(row['avg_novel_adjusted_reward'])/row['N']])

    # r = [i for i in e.index if 'VIRGIN' not in i]

    result.insert(9, 'V_U_Normalized', [float(result['V_U1'] / total)])
    result.insert(10, 'U_Normalized', [float(result['U1'] / total)])
    return result

def get_data_from_sql(agent_name, tournament_likeness):
    # a = f"SELECT * FROM {agent_name}_Results_View where Tournament_Name like '%{tournament_likeness}%'"
    if debug:
        a = f"SELECT TOP (10000) A.*, ZONE.* FROM {agent_name}_Results_View A LEFT JOIN LOOKUP_PERFORMANCE_ZONES ZONE on Zone.Agent_Name = '{agent_name}' and A.Tournament_Name like '%' + Zone.Tournament_Name + '%' where A.Tournament_Name like '%{tournament_likeness}%'"
    else:
        a = f"SELECT A.*, ZONE.* FROM {agent_name}_Results_View A LEFT JOIN LOOKUP_PERFORMANCE_ZONES ZONE on Zone.Agent_Name = '{agent_name}' and A.Tournament_Name like '%' + Zone.Tournament_Name + '%' where A.Tournament_Name like '%{tournament_likeness}%'"

    pm = PalMessenger(True, False)
    azure = AzureConnectionService(pm)
    if azure.is_connected():
        return pd.read_sql(a, azure.sql_connection)

# pm = PalMessenger(True, False)
#
# azure = AzureConnectionService(pm)
#
# a = "SELECT TOP (10000) * FROM TUFTS_AGENT_TEST_V3_Results_View where Tournament_Name like '%062622'"
#
# df = pd.read_sql(a, azure.sql_connection)
# print(df)
# Get Baseline:
def get_data():
    # baselineA = get_data_from_sql("TUFTS_AGENT_TEST_V3", 'POGO_L00_T01_S01_VIRGIN_X0100_A_U9999_V0_062322')
    baselineA = get_data_from_sql("SIFT_AGENT_TEST_V6", 'POGO_L00_T01_S01_VIRGIN_X0100_A_U9999_V0_062611')
    # baselineA = df[df['Tournament_Name'] == 'POGO_L00_T01_S01_VIRGIN_X0100_A_U9999_V1_062611']
    baselineA.insert(0, 'type', 'VIRGIN')

    baselineA = baselineA.drop("Agent_Name", axis=1)

    #get other data:
    df = get_data_from_sql("SIFT_AGENT_TEST_V6", "062611")
    # df = get_data_from_sql("TUFTS_AGENT_TEST_V3", "062622")

    # Ignore Virgin Tournaments
    remainder = df[~df['Tournament_Name'].str.contains('VIRGIN')]

    remainder = remainder.drop("Agent_Name", axis=1)

    answers = remainder.groupby('Tournament_Name').apply(lambda grp: stack_baseline(grp, baselineA))
    # answers.to_csv("TUFTS_Pre_Novelty_Base_070722_Dense.csv")
    answers.to_csv("SIFT_Pre_Novelty_Base_070814_AVG.csv")
    print(answers)


# get_data()

def upload_to_sql(csv_file, tbl_name='LOOKUP_PERFORMANCE_ZONES'):
    df = pd.read_csv(csv_file)
    rows_to_add = []
    for index, row in df.iterrows():
        rows_to_add.append(row.to_dict())

    uploads = []
    for dict in rows_to_add:
        uploads.extend([tuple(dict.values())])

    pm = PalMessenger(True, False)
    azure = AzureConnectionService(pm)
    if azure.is_connected():
        cursor = azure.sql_connection.cursor()
        # replace rows where this agent & tournament exist
        a = df.groupby(['TOURNAMENT_NAME', 'Agent_Name'])
        for name, groups in a:
            cursor.execute(f"""
                SELECT *
                FROM {tbl_name}
                WHERE TOURNAMENT_NAME = '{name[0]}' and Agent_Name = '{name[1]}'
            """)
            if cursor.fetchone() is not None:
                print(f"Deleting entries from {tbl_name}: TOURNAMENT_NAME = '{name[0]}' and Agent_Name = '{name[1]}'")
                cursor.execute(f"""
                    DELETE FROM {tbl_name}
                    WHERE TOURNAMENT_NAME = '{name[0]}' and Agent_Name = '{name[1]}'
                """)
                azure.sql_connection.commit()
            else:
                continue

        r = f"""INSERT INTO {tbl_name} 
                ({', '.join([i for i in rows_to_add[0].keys()])}) 
                VALUES ({', '.join(['?' for i in uploads[0]])}) 
            ;"""

        cursor.executemany(r, uploads)
        azure.sql_connection.commit()


# file = "/Users/dnarayanan/currentproj/sail_on/database_extracts/performance_zone_lookup_uploads/SIFT_V6_063016.csv"
# file = "/Users/dnarayanan/currentproj/sail_on/database_extracts/performance_zone_lookup_uploads/GT_POGO_V3_063016.csv"
# tbl_name = "LOOKUP_PERFORMANCE_ZONES"
#
# upload_to_sql(file, tbl_name)

if __name__ == '__main__':
    debug = False
    get_data()