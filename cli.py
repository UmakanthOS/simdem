# A console based UI for SimDem.

import difflib
import os
import pexpect
import pexpect.replwrap
import random
import time
import sys
import colorama
import config
colorama.init(strip=None)

PEXPECT_PROMPT = u'[PEXPECT_PROMPT>'
PEXPECT_CONTINUATION_PROMPT = u'[PEXPECT_PROMPT+'

class Ui(object):
    _shell = None
    demo = None

    def __init__(self):
        pass

    def prompt(self):
        """Display the prompt for the user. This is intended to indicate that
        the user is expected to take an action at this point.
        """
        self.display(config.console_prompt, colorama.Fore.WHITE)

    def command(self, text):
        """Display a command, or a part of a command tp be executed."""
        self.display(text, colorama.Fore.WHITE + colorama.Style.BRIGHT)
        
    def results(self, text):
        """Display the results of a command execution"""
        self.display(text, colorama.Fore.GREEN + colorama.Style.BRIGHT, True)
        
    def heading(self, text):
        """Display a heading"""
        self.display(text, colorama.Fore.CYAN + colorama.Style.BRIGHT, True)
        print()
        
    def description(self, text):
        """Display some descriptive text. Usually this is text from the demo
        document itself.

        """
        self.display(text, colorama.Fore.CYAN)
 
    def information(self, text, new_line = False):
        """Display some informative text. Usually this is content generated by
        SimDem. Do not print a new line unless new_line == True.

        """
        self.display(text, colorama.Fore.WHITE, new_line)

    def prep_step(self, step):
        """Displays a preparation step item.
        """
        self.display(step["title"], colorama.Fore.MAGENTA, True)
        
    def next_step(self, index, title):
        """Displays a next step item with an index (the number to be entered
to select it) and a title (to be displayed).
        """
        self.display(index, colorama.Fore.CYAN)
        self.display(title, colorama.Fore.CYAN, True)
        
    def instruction(self, text):
        """Display an instruction for the user.
        """
        self.display(text, colorama.Fore.MAGENTA, True)    

    def warning(self, text):
        """Display a warning to the user.
        """
        self.display(text, colorama.Fore.RED + colorama.Style.BRIGHT, True)

    def new_para(self):
        """Starts a new paragraph."""
        self.new_line()
        self.new_line()

    def new_line(self):
        """Move to the next line"""
        print()
        
    def horizontal_rule(self):
        print("\n\n============================================\n\n")

    def clear(self):
        """Clears the screen ready for  anew section of the script."""
        if self.demo.is_simulation:
            self.demo.current_command = "clear"
            self.simulate_command()
        else:        
            self.run_command("clear")
        self.prompt()
        
    def display(self, text, color, new_line=False):
        """Display some text in a given color. Do not print a new line unless
        new_line is set to True.

        """
        print(color, end="")
        print(text, end="", flush=True)
        if new_line:
            print(colorama.Style.RESET_ALL)
        else:
            print(colorama.Style.RESET_ALL, end="")

    def log(self, level, text):
        if config.is_debug:
            print(level.upper() + " : " + text)
            
    def request_input(self, text):
        """Displays text that is intended to propmt the user for 
        input and then waits for input.

        """
        print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT, end="")
        print(text)
        print(colorama.Style.RESET_ALL, end="")
        return self.input_string().lower()
        
    def input_interactive_variable(self, name):
        """
        Gets a value from stdin for a variable.
        """
        print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT, end="")
        print("\n\nEnter a value for ", end="")
        print(colorama.Fore.YELLOW + colorama.Style.BRIGHT, end="")
        print("$" + name, end="")
        print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT, end="")
        print(": ", end="")
        print(colorama.Fore.WHITE + colorama.Style.BRIGHT, end="")
        value = input()
        return value

    def type_command(self):
        """
        Displays the command on the screen
        If simulation == True then it will look like someone is typing the command
        """

        text = ""
        end_of_var = 0
        current_command, var_list = self.demo.get_current_command()
        for idx, char in enumerate(current_command):
            if char != "\n":
                text += char

        if self.demo.is_simulation:
            for char in text:
                delay = random.uniform(0.02, config.TYPING_DELAY)
                time.sleep(delay)
                self.command(char)
        else:
            self.command(text)
                    

    def simulate_command(self, silent = False):
        """Types the current command on the screen, executes it and outputs
        the results if simulation == True then system will make the
        "typing" look real and will wait for keyboard entry before
        proceeding to the next command.

        If silent = True then the command and its results will not be
        ouptut.

        """
        
        self.log("debug", "Simulating command: '" + self.demo.current_command + "'")
        if not self.demo.is_learning or self.demo.current_command.strip() == "clear":
            self.type_command()
            _, var_list = self.demo.get_current_command()

            # Get values for unknown variables
            for var_name in var_list:
                if (self.demo.is_testing):
                    var_value = "Dummy value for test"
                else:
                    var_value = self.input_interactive_variable(var_name)
                if not var_name.startswith("SIMDEM_"):
                    self.demo.env.set(var_name, var_value)
                    self.run_command(var_name + '="' + var_value + '"')

            output = self.run_command()
            self.demo.last_command = self.demo.current_command
            self.demo.current_command = ""
        else:
            done = False
            while not done:
                print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT, end="")
                print("\nType the command '", end = "")
                print(colorama.Fore.WHITE + colorama.Style.BRIGHT, end="")
                print(self.demo.current_command.strip(), end = "")
                print(colorama.Fore.MAGENTA + colorama.Style.BRIGHT, end="")
                print("'")
                print("\t- type 'auto' (or 'a') to automatically type the command")
                print(colorama.Fore.WHITE + colorama.Style.BRIGHT, end="")
                print("\n$ ", end = "", flush = True)
                typed_command = input()
                if typed_command.lower() == "a" or typed_command.lower() == "auto":
                    self.demo.is_learning = False
                    output = self.simulate_command()
                    self.demo.is_learning = True
                    done = True
                elif typed_command == self.demo.current_command.strip():
                    self.demo.is_learning = False
                    output = self.simulate_command()
                    self.demo.is_learning = True
                    done = True
                else:
                    print(colorama.Fore.RED, end="")
                    print("You have a typo there")

        self.log("debug", "Output: '" + output +"'")
        return output

    def input_string(self):
        """ Get a string from the user."""
        return input()
    
    def get_shell(self):
        """Gets or creates the shell in which to run commands for the
        supplied demo
        """
        if self._shell == None:
            child = pexpect.spawnu('/bin/bash', env=self.demo.env.get(), echo=False, timeout=None)
            ps1 = PEXPECT_PROMPT[:5] + u'\[\]' + PEXPECT_PROMPT[5:]
            ps2 = PEXPECT_CONTINUATION_PROMPT[:5] + u'\[\]' + PEXPECT_CONTINUATION_PROMPT[5:]
            prompt_change = u"PS1='{0}' PS2='{1}' PROMPT_COMMAND=''".format(ps1, ps2)
            self._shell = pexpect.replwrap.REPLWrapper(child, u'\$', prompt_change)
        return self._shell

    def run_command(self, command=None, silent = False):
        """
        Run the self.demo.curent_command unless command is passed in, in
        which case run the supplied command in the current demo
        environment. Return the output of the command.
        """
        if not command:
            command = self.demo.current_command

        self.new_line();

        self.log("debug", "Execute command: '" + command + "'")
        start_time = time.time()
        response = self.get_shell().run_command(command)
        end_time = time.time()

        if not silent:
            self.results(response)

        if self.demo.is_testing:
            self.information("--- %s seconds execution time ---" % (end_time - start_time), True)

        return response

    def get_help(self):
        help = []
        help.append("SimDem Help")
        help.append("===========")
        help.append("")
        help.append("Pressing any key other than those listed below will result in the script progressing")
        help.append("")
        help.append("b           - break out of the script and accept a command from user input")
        help.append("b -> CTRL-C - stop the script")
        help.append("d           - (redisplay the description that precedes the current command then resume from this point)")
        help.append("r           - repeat the previous command")
        help.append("h           - displays this help message")
        help.append("")
        return help
    
    def check_for_interactive_command(self):
        """Wait for a key to be pressed.

        Most keys result in the script
        progressing, but a few have special meaning. See the
        documentation or code for a description of the special keys.
        """
        if not self.demo.is_automated:
            if not self.demo.is_simulation:
                self.instruction("Press a command key to proceed (h for help)")
            key = self.get_instruction_key()

            if key == 'h':
                text = self.get_help()
                for line in text:
                    self.information(line, True)

                self.check_for_interactive_command()
            elif key == 'b':
                command = input()
                self.run_command(command)
                self.prompt()
                self.check_for_interactive_command()
            elif key == 'd':
                print("")
                print(colorama.Fore.CYAN) 
                print(self.demo.current_description);
                print(colorama.Style.RESET_ALL)
                self.prompt()
                print(self.demo.current_command, end="", flush=True)
                self.check_for_interactive_command()
            elif key == 'r':
                if not self.demo.last_command == "":
                    self.demo.current_command = self.demo.last_command
                    self.simulate_command()
                    self.prompt()
                    self.check_for_interactive_command()

    def get_instruction_key(self):
        """Waits for a single keypress on stdin.

        This is a silly function to call if you need to do it a lot because it has
        to store stdin's current setup, setup stdin for reading single keystrokes
        then read the single keystroke then revert stdin back after reading the
        keystroke.

        Returns the character of the key that was pressed (zero on
        KeyboardInterrupt which can happen when a signal gets handled)

        This method is licensed under cc by-sa 3.0 
        Thanks to mheyman http://stackoverflow.com/questions/983354/how-do-i-make-python-to-wait-for-a-pressed-key\
        """
        import termios, fcntl, sys, os
        fd = sys.stdin.fileno()
        # save old state
        flags_save = fcntl.fcntl(fd, fcntl.F_GETFL)
        attrs_save = termios.tcgetattr(fd)
        # make raw - the way to do this comes from the termios(3) man page.
        attrs = list(attrs_save) # copy the stored version to update
        # iflag
        attrs[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK 
                      | termios.ISTRIP | termios.INLCR | termios. IGNCR 
                      | termios.ICRNL | termios.IXON )
        # oflag
        attrs[1] &= ~termios.OPOST
        # cflag
        attrs[2] &= ~(termios.CSIZE | termios. PARENB)
        attrs[2] |= termios.CS8
        # lflag
        attrs[3] &= ~(termios.ECHONL | termios.ECHO | termios.ICANON
                      | termios.ISIG | termios.IEXTEN)
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        # turn off non-blocking
        fcntl.fcntl(fd, fcntl.F_SETFL, flags_save & ~os.O_NONBLOCK)
        # read a single keystroke
        try:
            ret = sys.stdin.read(1) # returns a single character
        except KeyboardInterrupt:
            ret = 0
        finally:
            # restore old state
            termios.tcsetattr(fd, termios.TCSAFLUSH, attrs_save)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags_save)
        return ret

    def test_results(self, expected_results, actual_results, similarity, expected_similarity = 0.66):
        """Display the test results for a single test
        """
        print("\n\n=============================\n\n")
        print(colorama.Fore.RED + colorama.Style.BRIGHT)
        print("FAILED")
        print(colorama.Style.RESET_ALL)
        print("Similarity ratio:    " + str(similarity))
        print("Expected Similarity: " + str(expected_similarity))
        print("\n\n=============================\n\n")
        print("Expected results:")
        print(colorama.Fore.GREEN + colorama.Style.BRIGHT)
        print(expected_results)
        print(colorama.Style.RESET_ALL)
        print("Actual results:")
        print(colorama.Fore.RED + colorama.Style.BRIGHT)
        print(actual_results)
        print(colorama.Style.RESET_ALL)
        print("\n\n=============================\n\n")
        print(colorama.Style.RESET_ALL)

    def get_command(self, commands):
        cmd = self.request_input("What mode do you want to run in? (default 'tutorial')")

        if cmd == "":
            cmd = "tutorial"
        while not cmd in commands:
            cmd = self.get_command(commands)
        return cmd

    def set_demo(self, demo):
        self.demo = demo
