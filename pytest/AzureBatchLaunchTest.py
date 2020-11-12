import unittest
import pprint
import os
from AzureBatch.AzureBatchLaunchTournaments import *
from AzureBatch.AgentBatchCommands import *

#    launch_g10_tournaments("GT_Trained_HUGA_1_V1",
#                            AgentType.GT_HG_BASELINE,
#                            TestType.STAGE4,
#                            global_config,
#                            pool="HUGA_GT_Baseline_1_X10",
#                            suffix="_060821")

class MyTestCase(unittest.TestCase):

    def test_g10_tournaments2(self, name, agentType, testType, pool, suffix, tournament_directory):
        # def launch_g10_tournaments(agent, agentType, test_type, global_config, suffix):
        vals = get_tournaments(testType, tournament_directory)
        if testType == TestType.STAGE4:
            self.assertEqual(len(vals), 5)
        elif testType == TestType.STAGE5:
            self.assertEqual(len(vals), 3)
        elif testType == TestType.STAGE6:
            self.assertEqual(len(vals), 1)
        else:
            self.assertEqual(True, False)

        #for folder in output:

            # agent_pool = AzureBatchLaunchTournaments(agent, agentType, folder, global_config, suffix)
            # agent_pool.execute_sample()

    def expected_number_of_tests(self, testType,tournament_directory, num_tests):
        vals = get_tournaments(testType, tournament_directory)
        self.assertEqual(len(vals), num_tests)



    # def test_something(self):
    #     self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
    # MyTestCase
