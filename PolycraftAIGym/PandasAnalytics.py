from PolycraftAIGym.AzureConnectionService import AzureConnectionService
from PolycraftAIGym.PalMessenger import PalMessenger
import pandas as pd
import numpy as np

def stack_baseline(group):
    # group.loc[:, 'type'] = 'NOVEL'
    # group = remainder[remainder['Tournament_Name'] ==  'POGO_L01_T01_S01_AXE_X0100_A_U0014_V2_062611']
    group.insert(0, 'type', 'NOVEL')

    r = pd.concat([group, baselineA])
    r['rank'] = r['Final_Reward'].rank(method='dense')
    # r.loc[r.type == 'VIRGIN', 'r_sum_base'] = r.rank
    # r.loc[r.type == 'NOVEL', 'r_sum_novel'] = r.rank
    r['r_sum_base'] = r.apply(lambda f: (f['rank']) * np.where(f['type'] == 'VIRGIN', 1, 0), axis=1)
    r['r_sum_novel'] = r.apply(lambda f: (f['rank']) * np.where(f['type'] == 'NOVEL', 1, 0), axis=1)
    grouped = r.groupby('Tournament_Name')

    e = grouped.apply(lambda x: pd.Series(dict(
        avg_final_reward=x.Final_Reward.sum(),
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
            continue

        result.insert(4, 'R1', [row['R']])
        result.insert(5, 'N1', [row['N']])
        result.insert(6, 'U1', [(row['R'] - (row['N'] * (row['N'] + 1)) / 2)])

    # r = [i for i in e.index if 'VIRGIN' not in i]

    result.insert(7, 'V_U_Normalized', [float(result['V_U1'] / total)])
    result.insert(8, 'U_Normalized', [float(result['U1'] / total)])
    return result


def get_data_from_sql(agent_name, tournament_likeness):
    a = f"SELECT * FROM {agent_name}_Results_View where Tournament_Name like '%{tournament_likeness}%'"
    pm = PalMessenger(True, False)
    azure = AzureConnectionService(pm)
    if azure.is_connected():
        return pd.read_sql(a, azure.sql_connection)

# pm = PalMessenger(True, False)

# azure = AzureConnectionService(pm)
#
# a = "SELECT TOP (10000) * FROM TUFTS_AGENT_TEST_V3_Results_View where Tournament_Name like '%062622'"
#
# df = pd.read_sql(a, azure.sql_connection)
# print(df)
# Get Baseline:
def get_data():
    baselineA = get_data_from_sql("TUFTS_AGENT_TEST_V3", 'POGO_L00_T01_S01_VIRGIN_X0100_A_U9999_V1_062322')
    # baselineA = df[df['Tournament_Name'] == 'POGO_L00_T01_S01_VIRGIN_X0100_A_U9999_V1_062611']
    baselineA.insert(0, 'type', 'VIRGIN')

    #get other data:
    # df = get_data_from_sql("SIFT_AGENT_TEST_V6", "062611")
    df = get_data_from_sql("TUFTS_AGENT_TEST_V3", "062622")

    # Ignore Virgin Tournaments
    remainder = df[~df['Tournament_Name'].str.contains('VIRGIN')]

    answers = remainder.groupby('Tournament_Name').apply(lambda grp: stack_baseline(grp))
    answers.to_csv("TUFTS_AGENT_RESULTS_Pre_Novelty_Base_063014.csv")
    print(answers)


def upload_to_sql(csv_file, tbl_name):
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
file = "/Users/dnarayanan/currentproj/sail_on/database_extracts/performance_zone_lookup_uploads/GT_POGO_V3_063016.csv"
tbl_name = "LOOKUP_PERFORMANCE_ZONES"

upload_to_sql(file, tbl_name)