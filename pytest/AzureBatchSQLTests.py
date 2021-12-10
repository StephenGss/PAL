import unittest
import os,sys

# https://stackoverflow.com/questions/25827160/importing-correctly-with-pytest
sys.path.append(os.path.realpath(os.path.dirname(__file__) + "\\..\\PolycraftAIGym"))
print(sys.path)
import PolycraftAIGym.config as config
import PolycraftAIGym.AzureConnectionService
import PolycraftAIGym.PalMessenger


class MyTestCase(unittest.TestCase):

    def test_sql_drivers(self):
        # https://stackoverflow.com/questions/5971312/how-to-set-environment-variables-in-python
        os.environ['CONDA_PREFIX'] = "/dummy"
        acn = PolycraftAIGym.AzureConnectionService.AzureConnectionService(
            PolycraftAIGym.PalMessenger.PalMessenger(True, False),
            use_global_configs=True
        )
        self.assertEqual(True, acn.is_connected())

    def test_sql_upload(self, uploadID=16):
        """
        Test confirms that we can upload to the REGRESSION_TEST_AGGREGATE table with the correctly formatted params
        :param uploadID: Arbitrary ID to run the test with to insure that the test will not fail on attempting to
        re-upload the same primary key.
        """
        os.environ['CONDA_PREFIX'] = "/dummy"
        acn = PolycraftAIGym.AzureConnectionService.AzureConnectionService(
            PolycraftAIGym.PalMessenger.PalMessenger(True, False),
            use_global_configs=True
        )
        score_dict = {0: {
            'game_path': "/test/1234",
            'timestamp': PolycraftAIGym.PalMessenger.PalMessenger.time_now_str(format='%Y%m%d %H:%M:%S'),
            'RegID': f"{uploadID}",
            'passFail': 0,
            'responses': "TestReponseString",
            }
        }
        self.assertEqual(acn.send_regression_test_to_azure(score_dict, 0), True)


    # def test_something(self):
    #     self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
