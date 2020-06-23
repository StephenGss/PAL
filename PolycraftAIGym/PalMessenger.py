from pathlib import Path
import time, re


class PalMessenger:
    """ Isolates message handling and allows easy piping into the console or a log file"""
    def __init__(self, print_log_info, write_log_info, log_file=None, log_note="", give_time=True):
        # Flag for sending messages to the console
        self.print_log_info = print_log_info
        # Flag for writing messages to a log file
        self.write_log_info = write_log_info
        # File name, including path for the log file
        self.log_file = log_file
        # For differentiating Pal Messenger sources in console or logs
        # Intended strings are "SENT: ", "RCVD: ", "END: ", or nothing
        self.log_note = log_note
        # If give_time is true, a time stamp will automatically be appended to all messages
        self.give_time = give_time
        if write_log_info is True:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    def __copy__(self):
        return PalMessenger(self.print_log_info, self.write_log_info, self.log_file, self.log_note, self.give_time)

    def message_strip(self, message_to_handle):
        """
        We don't care about the "blockInFront" array! Let's strip it out!
        :param message_to_handle: raw msg
        :return:
        """
        message = ""
        if self.give_time:
            message = message + PalMessenger.time_now_str() + ": "

        p = re.compile('(.*\[CLIENT\]{"blockInFront":{).*(},"goal".*)')
        msg_stripped = p.sub("\g<1>REDACTED\g<2>", str(message_to_handle))
        message = message + self.log_note + msg_stripped
        if self.print_log_info:
            print(message)
        message = message + "\n"
        if self.write_log_info:
            with open(self.log_file, "a") as write_file:
                write_file.write(message)

    def message(self, message_to_handle):
        message = ""
        if self.give_time:
            message = message + PalMessenger.time_now_str() + ": "
        message = message + self.log_note + str(message_to_handle)
        if self.print_log_info:
            print(message)
        if not message.endswith("\\n"):
            message = message + "\n"
        if self.write_log_info:
            with open(self.log_file, "a") as write_file:
                write_file.write(message)

    @staticmethod
    def time_now_str(sep=":"):
        """
        Adjust the Default to match the ANSI standard for Time Stamps - makes it easy to convert to DateTime in SQL
        :param sep: separator for minutes
        :return: current GMT, formatted for ease of use in Database
        """
        format = "%Y-%m-%d_%H" + sep + "%M" + sep + "%S"
        return time.strftime(format, time.gmtime())