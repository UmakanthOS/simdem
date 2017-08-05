from flask import Flask, send_from_directory
from flask import render_template
from flask.ext.socketio import SocketIO, emit
import threading
import time

from cli import Ui
import config

ui = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
thread = None
command_key = None
url = "http://localhost:8080"
    
def background_thread():
    while True:
        socketio.sleep(10)
        text = "I'm alive (background thread"

        socketio.emit('log',
                      text,
                      namespace='/console')

@socketio.on('connect', namespace='/console')
def connect():
    global thread
    global ui
    while ui is None:
        time.sleep(0.25)

    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
        ui.ready = True

@socketio.on('ping', namespace='/console')
def ping_pong():
    emit('pong')

@socketio.on('command_key', namespace='/console')
def got_command_key(key):
    global command_key
    command_key = key
    
@app.route('/js/<path:filename>')
def send_js(filename):
    return send_from_directory('js', filename)

@app.route('/style/<path:filename>')
def send_style(filename):
    return send_from_directory('style', filename)

@app.route('/')
def index():
    return render_template('index.html', console = "Initializing...")

class WebUi(Ui):
    def __init__(self):
        global ui
        import logging
        logging.basicConfig(filename='error.log',level=logging.DEBUG)
        ui = self
        self.ready = False
        t = threading.Thread(target=socketio.run, args=(app, '0.0.0.0', '8080'))
        t.start()

    def prompt(self):
        """Display the prompt for the user. This is intended to indicate that
        the user is expected to take an action at this point.
        """
        self._send_to_console(config.console_prompt, "prompt")

    def command(self, text):
        """Display a command, or a part of a command tp be executed."""
        self._send_to_console(text, "command", False)

    def results(self, text):
        """Display the results of a command execution"""
        self._send_to_console(text, "results", True)
        
    def clear(self, demo):
        """Clears the console ready for a new section of the script."""
        if demo.is_simulation:
            # demo.current_command = "clear"
            # self.simulate_command(demo)
            raise Exception("Not implemented yet")
        else:        
            socketio.emit('clear',
                          namespace='/console')

    def heading(self, text):
        """Display a heading"""
        self._send_to_info(text, "heading", True)
        self.new_line()

    def description(self, text):
        """Display some descriptive text. Usually this is text from the demo
        document itself.

        """
        # fixme: color self.display(text, colorama.Fore.CYAN)
        self._send_to_info(text, "description", True)

    def next_step(self, index, title):
        """Displays a next step item with an index (the number to be entered
to select it) and a title (to be displayed).
        """
        self._send_to_info(str(index) + " " + title, "next_step", True)

    def instruction(self, text):
        """Display an instruction for the user.
        """
        self._send_to_info(text, "instruction", True)
    
    def warning(self, text):
        """Display a warning to the user.
        """
        self._send_to_info(text, "warning", True)

    def new_para(self, div = "console"):
        """Starts a new paragraph in the indicated div."""
        self.new_line(div)
        self.new_line(div)

    def new_line(self, div = "console"):
        """Send a single new line to te indicated div"""
        if div == "console":
            self._send_to_console("<br/>")
        elif div == "info":
            self._send_to_info("<br/>")
            
    def horizontal_rule(self):
        self._send_to_info("<br/><br/>============================================<br/><br/>")

    def display(self, text, color, new_line=False):
        """Display some text in a given color. Do not print a new line unless
        new_line is set to True.

        """
        self._send_to_info(text, color, new_line)
        
    def request_input(self, text):
        """ Displays text that is intended to propmt the user for input. """
        self._send_to_info(text, "request_input", True)
        
    def _send_to_console(self, text, css_class = "description", new_line = False):
        """ Send a string to the console. If new_line is set to true then also send a <br/> """
        html = "<span class='" + css_class + "'>" + text + "</span>"
        if new_line:
            html += "<br/>"
            
        socketio.emit('update_console',
                      html,
                      namespace='/console')

    def _send_to_info(self, text, css_class = "description", new_line = False):
        """ Send a string to the console. If new_line is set to true then also send a <br/> """
        html = "<span class='" + css_class + "'>" + text + "</span>"
        if new_line:
            html += "<br/>"
            
        socketio.emit('update_info',
                      html,
                      namespace='/console')

    def get_instruction_key(self):
        """Gets an instruction from the user. See get_help() for details of
        relevant keys to respond with.

        """
        global command_key
        command_key = None
        socketio.emit('get_command_key',
                      namespace='/console')
        while command_key is None:
            return command_key

    def get_command(self):
        self.request_input("What mode do you want to run in? (default 'tutorial')")
        mode = ""
        # mode = input()
        if mode == "":
            mode = "tutorial"
        return mode
    



