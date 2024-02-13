import sys

if __name__ == '__main__':
	print('Please run main.py to start the program!')
	sys.exit()

import os
import platform
import traceback
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font
import tkinter.messagebox
import tkinter.filedialog

# for PyInstaller binaries
try:
	temp_path = sys._MEIPASS
except AttributeError:
	temp_path = os.getcwd()

# TODO: add more main modules here
import json
import urllib.request
import threading
import webbrowser
import configparser
import pkg_resources

pg_name = 'PyU8ROP'  # program name here

username = 'fxesdev'  # GitHub username here
repo_name = 'pyu8rop'  # GitHub repository name here

version = '0.1.0'  # displayed version (e.g. 1.0.0 Prerelease - must match GH release title)
internal_version = 'v0.1.0'  # internal version (must match GitHub release tag)
prerelease = False  # prerelease flag (must match GitHub release's prerelease flag)


def report_error(self=None, exc=None, val=None, tb=None, term=True):
	"""
	Logs in the console and displays a dialog box showing the error.
	Replaces the report_callback_exception() function in
	the tkinter.Tk class.
	NOTE: DO NOT REMOVE THE UNUSED ARGUMENTS! Due to the function replacement
	these arguments must be added.
	"""

	e = traceback.format_exc()
	err_text = f'''\
Whoops! An error has occurred.
{e}
If this error persists, please report it here:
https://github.com/{username}/{repo_name}/issues\
'''

	print(err_text)
	tk.messagebox.showerror('Whoops!', err_text)
	if term:
		sys.exit()


tk.Tk.report_callback_exception = report_error


class GUI:
	def __init__(self, window):
		self.version = version

		self.window = window

		self.temp_path = temp_path

		# change width and height of window here
		self.display_w = 800
		self.display_h = 600

		# TODO: add more "open" bools for other Toplevel classes
		self.updater_win_open = False

		tk_font = tk.font.nametofont('TkDefaultFont').actual()
		self.font_name = tk_font['family']
		self.font_size = tk_font['size']

		# TODO: add more font styles (italic, condensed, etc.)
		self.bold_font = (self.font_name, self.font_size, 'bold')

		self.init_window()
		self.init_protocols()

		self.gadgets = {}

		# updater settings
		self.auto_check_updates = tk.BooleanVar()
		self.auto_check_updates.set(True)
		self.check_prerelease_version = tk.BooleanVar()
		self.check_prerelease_version.set(False)

		self.debug = False

		# gets appdata folder
		if os.name == 'nt':
			self.appdata_folder = f'{os.getenv("LOCALAPPDATA")}\\{pg_name}'
		else:
			if platform.system() == 'Darwin':
				self.appdata_folder = os.path.expanduser(f'~/Library/Application Support/{pg_name}')
			else:
				self.appdata_folder = os.path.expanduser(f'~/.config/{pg_name}')

		self.save_to_cwd = False
		self.ini = configparser.ConfigParser()
		self.parse_settings()

		self.refreshing = True

		# TODO: add more toplevel classes
		self.UpdaterGUI = UpdaterGUI(self)

		self.unsupported_tcl = False
		if sys.version_info < (3, 7, 6):
			if tk.messagebox.askyesno('Warning', f'''
It looks like you are running Python {platform.python_version()}, which has a version of Tcl/Tk that doesn\'t support \
some Unicode characters.

Do you want to continue?\
''', icon='warning'):
				self.unsupported_tcl = True
			else:
				self.quit()

		self.menubar()

	def start_main(self):
		"""
		Runs necessary commands before calling the main function.
		"""

		# TODO: add more commands here

		self.updates_checked = False

		if self.auto_check_updates.get():
			threading.Thread(target=self.auto_update).start()
		else:
			self.updates_checked = True

		ttk.Label(text = 'Gadget list\n', font = self.bold_font).pack()

		buttonframe = FocusFrame()
		ttk.Button(buttonframe, text = 'Add gadget', command = self.add_gadget).pack(side = 'left')
		self.clearbutton = ttk.Button(buttonframe, text = 'Delete all gadgets', command = self.clear_all, state = 'disabled'); self.clearbutton.pack(side = 'left')
		buttonframe.pack()

		self.gadgetframe = VerticalScrolledFrame(self.window)
		self.gadgetframe.pack(fill = 'both', expand = True)

		self.main()

	def add_gadget(self, type_ = 'address', data = None):
		if type_ == 'address': wclass = Address
		#elif type_ == 'pop': wclass = Pop
		else:
			self.n_a()
			return

		idx = max(self.gadgets) + 1 if len(self.gadgets) > 0 else 0
		if len(self.gadgets) == 0: self.clearbutton['state'] = 'normal'

		widget = wclass(self.gadgetframe.interior, self, idx, data)
		self.gadgets[idx] = {'type': type_, 'data': data, 'widget': widget}
		widget.pack(fill = 'x')

	def clear_all(self):
		if tk.messagebox.askyesno('Warning', 'Are you sure you want to delete all gadgets?', icon = 'warning'):
			for j in [i['widget'] for i in self.gadgets.values()]: j.destroy()

	@staticmethod
	def validate_hex(new_char, new_str, act_code, rang = None, spaces = False):
		act_code = int(act_code)
		if rang: rang = eval(rang)
		
		if act_code == 1:
			try: new_value_int = int(new_char, 16)
			except ValueError:
				if len(new_char) == 1:
					if new_char != ' ': return False
					elif not spaces: return False
				else:
					try: new_value_int = int(new_char.replace(' ', ''), 16)
					except ValueError: return False
			if rang:
				if len(new_str) > len(hex(rang[-1])[2:]): return False
				elif len(new_str) == len(hex(rang[-1])[2:]) and int(new_str, 16) not in rang: return False

		return True

	def open(self):
		f = tk.filedialog.askopenfile(mode = 'rb', filetypes = [('All Files', '*.*'), ('Binary Files', '*.bin')], defaultextension = '.bin')
		if f is not None:
			bytecode = f.read()
			for i in range(0, len(bytecode), 4):
				data = int.from_bytes(bytecode[i:i+4], 'little')
				self.add_gadget(data = data & 0xffffe)

	def auto_update(self):
		self.update_thread = ThreadWithResult(target=self.UpdaterGUI.updater.check_updates, args=(True,))
		self.update_thread.start()
		i = 0
		j = 0
		mult = 5000
		while self.update_thread.is_alive():
			if i == mult * 4:
				i += 1
				j = 1
			else:
				i = i - 1 if j else i + 1
			if i == 0:
				j = 0
			print(' ' * (int(i / mult)) + '.' + ' ' * (5 - int(i / mult)), end='\r')
		print('\r     ', end='\r')
		update_info = self.update_thread.result
		if update_info['newupdate']:
			self.UpdaterGUI.init_window(True, (update_info['title'], update_info['tag'], update_info['prerelease'],
										update_info['body']))
		self.updates_checked = True

	def parse_settings(self):
		"""
		Loads the program settings.
		"""

		# load override settings
		if os.path.exists(os.path.join(os.getcwd(), 'settings.ini')):
			self.ini.read('settings.ini')
			self.save_to_cwd = True
		else:
			# load normal settings
			self.ini.read(f'{self.appdata_folder}\\settings.ini')

		sects = self.ini.sections()
		if sects:
			if 'settings' in sects:
				# TODO: add commands for loading settings
				pass

			if 'updater' in sects:
				try:
					self.auto_check_updates.set(self.ini.getboolean('updater', 'auto_check_updates'))
				except (configparser.NoSectionError, configparser.NoOptionError):
					pass
				try:
					self.check_prerelease_version.set(self.ini.getboolean('updater', 'check_prerelease_version'))
				except (configparser.NoSectionError, configparser.NoOptionError):
					pass

			if 'dont_touch_this_area_unless_you_know_what_youre_doing' in sects:
				try:
					self.debug = self.ini.getboolean('dont_touch_this_area_unless_you_know_what_youre_doing', 'debug')
				except (configparser.NoSectionError, configparser.NoOptionError):
					pass

		self.save_settings()

	def save_settings(self):
		"""
		Saves the program settings.
		"""

		# settings are set individually and initialized when needed to retain compatibility between versions
		if 'settings' not in self.ini.keys():
			self.ini['settings'] = {}

		# TODO: add commands for saving settings

		if 'updater' not in self.ini.keys():
			self.ini['updater'] = {}
		self.ini['updater']['auto_check_updates'] = str(self.auto_check_updates.get())
		self.ini['updater']['check_prerelease_version'] = str(self.check_prerelease_version.get())

		if 'dont_touch_this_area_unless_you_know_what_youre_doing' not in self.ini.keys():
			self.ini['dont_touch_this_area_unless_you_know_what_youre_doing'] = {}
		self.ini['dont_touch_this_area_unless_you_know_what_youre_doing']['debug'] = str(self.debug)

		if self.save_to_cwd:
			with open(os.path.join(os.getcwd(), 'settings.ini'), 'w') as f:
				self.ini.write(f)

		if not os.path.exists(self.appdata_folder):
			os.makedirs(self.appdata_folder)
		with open(f'{self.appdata_folder}\\settings.ini', 'w') as f:
			self.ini.write(f)

	@staticmethod
	def n_a():
		"""
		Used to prevent access to unimplemented or unfinished features.
		"""

		tk.messagebox.showinfo('Not implemented',
							   f'This feature is not implemented into this version of {pg_name}. Sorry!')

	def set_title(self, custom_str=None):
		"""
		Sets the Tkinter window title.
		"""

		self.window.title(f'{pg_name} {version}{" - " + custom_str if custom_str is not None else ""}')

	def init_window(self):
		"""
		Initializes the Tkinter window.
		"""

		self.window.geometry(f'{self.display_w}x{self.display_h}')
		self.window.resizable(False, False)
		self.window.bind('<F12>', self.version_details)
		self.window.bind('<Control-O>', lambda x: self.open())
		self.window.bind('<Control-o>', lambda x: self.open())
		self.window.option_add('*tearOff', False)
		self.set_title()
		# TODO: uncomment this when you actually have an icon.ico/xbm file

	#         try:
	#             self.window.iconbitmap(f'{self.temp_path}\\icon.{"ico" if os.name == "nt" else "xbm"}')
	#         except tk.TclError:
	#             err_text = f'''\
	# Whoops! The icon file "icon.ico" is required.
	# Can you make sure the file is in "{self.temp_path}"?
	# {traceback.format_exc()}
	# If this problem persists, please report it here:
	# https://github.com/{username}/{repo_name}/issues\
	# '''
	#             print(err_text)
	#             tk.messagebox.showerror('Hmmm?', err_text)
	#             sys.exit()

	def init_protocols(self):
		"""
		Initializes protocols.
		"""

		self.window.protocol('WM_DELETE_WINDOW', self.quit)

	def quit(self):
		"""
		Quits the program.
		"""

		if not any([
			self.updater_win_open,
			# TODO: add other "open" bools here
		]):
			sys.exit()

	@staticmethod
	def about_menu():
		"""
		Shows basic information about the version, system and architecture, as well as the license of the project.
		"""

		nl = '\n'
		syst = platform.system()
		syst += ' x64' if platform.machine().endswith('64') else ' x86'
		tk.messagebox.showinfo(f'About {pg_name}', f'''\
{pg_name} - {version} ({'64' if sys.maxsize > 2 ** 31 - 1 else '32'}-bit) - Running on {syst}
Project page: https://github.com/{username}/{repo_name}
{nl + 'WARNING: This is a pre-release version, therefore it may have bugs and/or glitches.' + nl if prerelease else ''}
Licensed under the GNU GPL-v3 license
(LICENSE file available on the GitHub repository or included with source code)\
''')

	def version_details(self, event=None):
		"""
		Shows technical information about the Python installation and operating system.
		By default, it can be triggered via the F12 key.
		"""

		if self.debug:
			dnl = '\n\n'
			tk.messagebox.showinfo(f'{pg_name} version details', f'''\
{pg_name} {version}{" (prerelease)" if prerelease else ""}
Internal version: {internal_version}

Python version information:
Python {platform.python_version()} ({'64' if sys.maxsize > 2 ** 31 - 1 else '32'}-bit)
Tkinter (Tcl/Tk) version {self.window.tk.call('info', 'patchlevel')}\
{" (most Unicode chars not supported)" if self.unsupported_tcl else ""}

Operating system information:
{platform.system()} {platform.release()}
{'NT version: ' if os.name == 'nt' else ''}{platform.version()}
Architecture: {platform.machine()}{dnl + "Settings file is saved to working directory" if self.save_to_cwd else ""}\
''')

	def disable_debug(self):
		if tk.messagebox.askyesno('Warning',
								  'To re-enable debug mode you must set the debug flag to True in settings.ini.\nContinue?',
								  icon='warning'):
			self.debug = False
			self.save_settings()
			self.menubar()  # update the menubar

	def menubar(self):
		"""
		Sets up the menubar.
		"""

		menubar = tk.Menu()

		file_menu = tk.Menu(menubar)
		file_menu.add_command(label = 'New', accelerator = 'Ctrl+N', state = 'disabled')
		file_menu.add_command(label = 'Open...', accelerator = 'Ctrl+O', command = self.open)
		file_menu.add_command(label = 'Save', accelerator = 'Ctrl+S', state = 'disabled')
		file_menu.add_command(label = 'Save as...', accelerator = 'Ctrl+Shift+S', state = 'disabled')
		file_menu.add_separator()
		file_menu.add_command(label = 'Load ROM', accelerator = 'Ctrl+L', state = 'disabled')
		file_menu.add_separator()
		file_menu.add_command(label = 'Exit', command = self.quit)
		menubar.add_cascade(label='File', menu=file_menu)

		settings_menu = tk.Menu(menubar)
		# TODO: add more setting options
		updater_settings_menu = tk.Menu(settings_menu)
		updater_settings_menu.add_checkbutton(label='Check for updates on startup', variable=self.auto_check_updates,
											  command=self.save_settings)
		updater_settings_menu.add_checkbutton(label='Check for pre-release versions',
											  variable=self.check_prerelease_version,
											  command=self.save_settings)
		settings_menu.add_cascade(label='Updates', menu=updater_settings_menu)

		if self.debug:
			settings_menu.add_separator()
			debug_menu = tk.Menu(settings_menu)
			debug_menu.add_command(label='Version details', command=self.version_details, accelerator='F12')
			debug_menu.add_separator()
			debug_menu.add_command(label='Updater test', command=lambda: self.UpdaterGUI.init_window(debug=True))
			debug_menu.add_separator()
			debug_menu.add_command(label='Disable debug mode', command=self.disable_debug)
			settings_menu.add_cascade(label='Debug', menu=debug_menu)

		menubar.add_cascade(label='Settings', menu=settings_menu)

		help_menu = tk.Menu(menubar)
		help_menu.add_command(label='Check for updates', command=self.UpdaterGUI.init_window)
		help_menu.add_command(label=f'About {pg_name}', command=self.about_menu)
		menubar.add_cascade(label='Help', menu=help_menu)

		self.window.config(menu=menubar)

	def main(self):
		"""
		Where the mainloop is called.
		"""

		self.set_title('Experimental version')
		self.window.mainloop()


class UpdaterGUI:
	def __init__(self, gui):
		self.gui = gui

		self.after_ms = 100

		self.updater = Updater()

	def init_window(self, auto=False, auto_download_options=None, debug=False):
		if not self.gui.updater_win_open:
			self.gui.updater_win_open = True

			self.auto = auto
			self.debug = debug

			self.win = tk.Toplevel(self.gui.window)
			self.win.geometry('400x400')
			self.win.resizable(False, False)
			self.win.protocol('WM_DELETE_WINDOW', self.quit)
			self.win.title('Updater')
			# TODO: uncomment this when you actually have an icon.ico/xbm file
#             try:
#                 self.updater_win.iconbitmap(f'{self.gui.temp_path}\\icon.{"ico" if os.name == "nt" else "xbm"}')
#             except tk.TclError:
#                 err_text = f'''\
# Whoops! The icon file "icon.ico" is required.
# Can you make sure the file is in "{self.gui.temp_path}"?
# {traceback.format_exc()}
# If this problem persists, please report it here:
# https://github.com/{username}/{repo_name}/issues\
# '''
#                 print(err_text)
#                 tk.messagebox.showerror('Hmmm?', err_text)
#                 sys.exit()

			self.win.focus()
			self.win.grab_set()
			if self.debug:
				self.debug_menu()
			elif self.auto:
				self.win.after(0, lambda: self.draw_download_msg(*auto_download_options))
			else: self.main()

	def quit(self):
		self.win.grab_release()
		self.win.destroy()
		self.gui.updater_win_open = False
		if self.auto:
			self.auto = False
			self.gui.main()

	def main(self):
		self.update_thread = ThreadWithResult(target=self.updater.check_updates,
											  args=(self.gui.check_prerelease_version.get(),))

		self.draw_check()
		self.win.after(1, self.start_thread)
		self.win.mainloop()

	def debug_menu(self):
		ttk.Button(self.win, text='Check updates', command=self.main).pack()
		ttk.Button(self.win, text='Message test',
				   command=lambda: self.draw_msg('Updater message test.\nLine 2\nLine 3\nLine 4')).pack()
		ttk.Button(self.win, text='New update screen test',
				   command=lambda: self.draw_download_msg(version, internal_version, False, '''\
Hello! **This is a *test* of the updater\'s Markdown viewer**, made possible with the [Markdown](https://pypi.org/project/Markdown/), [`mdformat`](https://pypi.org/project/mdformat/), and [TkinterWeb](https://pypi.org/project/tkinterweb/) modules.

By the way, here\'s [TkTemplate](https://github.com/gamingwithevets/tktemplate), which is what this program was based on.

Also, you should check out the [Steveyboi/GWE Discord server](https://gamingwithevets.github.io/redirector/discord).\
''')).pack()
		ttk.Button(self.win, text='Quit', command=self.quit).pack(side='bottom')

	def start_thread(self):
		self.update_thread.start()
		while self.update_thread.is_alive():
			self.win.update_idletasks()
			self.progressbar['value'] = self.updater.progress
		self.progressbar['value'] = 100
		self.update_thread.join()
		update_info = self.update_thread.result

		if update_info['error']:
			if 'exceeded' in update_info and update_info['exceeded']:
				self.draw_msg('GitHub API rate limit exceeded! Please try again later.')
			elif 'nowifi' in update_info and update_info['nowifi']:
				self.draw_msg(
					'Unable to connect to the internet. Please try again\nwhen you have a stable internet connection.')
			elif 'prerelease' in update_info and update_info['prerelease']:
				self.draw_msg('Cannot get the latest release. Try enabling "Check for\npre-release versions" in Settings.')
			else:
				self.draw_msg('Unable to check for updates! Please try again later.')
		elif update_info['newupdate']:
			self.draw_download_msg(update_info['title'], update_info['tag'], update_info['prerelease'])
		else:
			self.draw_msg('You are already using the latest version.')

	def draw_check(self):
		for w in self.win.winfo_children():
			w.destroy()

		ttk.Label(self.win, text='Checking for updates...').pack()
		self.progressbar = ttk.Progressbar(self.win, orient='horizontal', length=100, mode='determinate')
		self.progressbar.pack()
		ttk.Label(self.win, text='DO NOT close the program\nwhile checking for updates',
				  justify='center', font=self.gui.bold_font).pack(side='bottom')

	def draw_msg(self, msg):
		if self.auto:
			self.gui.set_title()
			self.quit()
		else:
			for w in self.win.winfo_children():
				w.destroy()
			ttk.Label(self.win, text=msg, justify='center').pack()
			ttk.Button(self.win, text='Back', command=self.quit).pack(side='bottom')

	@staticmethod
	def package_installed(package):
		try:
			pkg_resources.get_distribution(package)
		except pkg_resources.DistributionNotFound:
			return False

		return True

	def draw_download_msg(self, title, tag, prever, body):
		if self.auto:
			self.win.deiconify()
			self.gui.set_title()
		for w in self.win.winfo_children():
			w.destroy()
		ttk.Label(self.win, justify='center', text=f'''\
An update is available!
Current version: {self.gui.version}{" (pre-release)" if prerelease else ""}
New version: {title}{" (pre-release)" if prever else ""}\
''').pack()
		ttk.Button(self.win, text='Cancel', command=self.quit).pack(side='bottom')
		ttk.Button(self.win, text='Visit download page',
				   command=lambda: self.open_download(tag)).pack(side='bottom')

		ttk.Label(self.win).pack()

		packages_missing = []
		for package in ('markdown', 'mdformat-gfm', 'tkinterweb'):
			if not self.package_installed(package):
				packages_missing.append(package)

		if packages_missing:
			ttk.Label(self.win,
				text=f'Missing package(s): {", ".join(packages_missing[:2])}{" and " + str(len(packages_missing) - 2) + " others" if len(packages_missing) > 2 else ""}',
				font=self.gui.bold_font).pack()
		else:
			import markdown
			import mdformat
			import tkinterweb

			html = tkinterweb.HtmlFrame(self.win, messages_enabled=False)
			html.load_html(
				markdown.markdown(mdformat.text(body)).replace('../..', f'https://github.com/{username}/{repo_name}'))
			html.on_link_click(webbrowser.open_new_tab)
			html.pack()

		if self.auto:
			self.win.deiconify()

	def open_download(self, tag):
		webbrowser.open_new_tab(f'https://github.com/{username}/{repo_name}/releases/tag/{tag}')
		self.quit()


class Updater:
	def __init__(self):
		self.username, self.reponame = username, repo_name
		self.request_limit = 5

		self.progress = 0
		self.progress_inc = 25

	def check_internet(self):
		try:
			self.request('https://google.com', True)
			return True
		except Exception:
			return False

	def request(self, url, testing=False):
		success = False
		for i in range(self.request_limit):
			try:
				r = urllib.request.urlopen(url)
				success = True
				break
			except urllib.error.HTTPError as e:
				r = e.fp
				success = True
			except urllib.error.URLError as e:
				if not testing:
					if not self.check_internet():
						return
		if success:
			if not testing:
				d = r.read().decode()
				return json.loads(d)

	def check_updates(self, pr):
		self.progress = 0

		if not self.check_internet():
			return {
				'newupdate': False,
				'error': True,
				'exceeded': False,
				'nowifi': True
			}
		try:
			versions = []
			if not self.check_internet():
				return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}

			response = self.request(f'https://api.github.com/repos/{self.username}/{self.reponame}/releases')
			if response is None:
				return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}

			for info in response:
				versions.append(info['tag_name'])

			# UPDATE POINT 1
			self.progress += self.progress_inc

			if internal_version not in versions:
				try:
					testvar = response['message']
					if 'API rate limit exceeded for' in testvar:
						return {
							'newupdate': False,
							'error': True,
							'exceeded': True
						}
					else:
						return {'newupdate': False, 'error': False}
				except Exception:
					return {'newupdate': False, 'error': False}
			if not self.check_internet():
				return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}

			# UPDATE POINT 2
			self.progress += self.progress_inc

			response = self.request(
				f'https://api.github.com/repos/{self.username}/{self.reponame}/releases/tags/{internal_version}')
			if response is None:
				return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}
			try:
				testvar = response['message']
				if 'API rate limit exceeded for' in testvar:
					return {
						'newupdate': False,
						'error': True,
						'exceeded': True
					}
				else:
					return {'newupdate': False, 'error': False}
			except Exception:
				pass

			currvertime = response['published_at']

			# UPDATE POINT 3
			self.progress += self.progress_inc

			if not pr:
				if not self.check_internet():
					return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}

				response = self.request(f'https://api.github.com/repos/{self.username}/{self.reponame}/releases/latest')
				if response is None:
					return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}
				try:
					testvar = response['message']
					if 'API rate limit exceeded for' in testvar:
						return {
							'newupdate': False,
							'error': True,
							'exceeded': True
						}
					else:
						return {'newupdate': False, 'error': True, 'prerelease': True}
				except Exception:
					pass
				if response['tag_name'] != internal_version and response['published_at'] > currvertime:
					return {
						'newupdate': True,
						'prerelease': False,
						'error': False,
						'title': response['name'],
						'tag': response['tag_name'],
						'body': response['body']
					}
				else:
					return {
						'newupdate': False,
						'unofficial': False,
						'error': False
					}
			else:
				for ver in versions:
					if not self.check_internet():
						return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}

					response = self.request(
						f'https://api.github.com/repos/{self.username}/{self.reponame}/releases/tags/{ver}')
					if response is None:
						return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': True}
					try:
						testvar = response['message']
						if 'API rate limit exceeded for' in testvar:
							return {
								'newupdate': False,
								'error': True,
								'exceeded': True
							}
						else:
							return {'newupdate': False, 'error': True, 'exceeded': False, 'nowifi': False}
					except Exception:
						pass
					if currvertime < response['published_at']:
						return {
							'newupdate': True,
							'prerelease': response['prerelease'],
							'error': False,
							'title': response['name'],
							'tag': response['tag_name'],
							'body': response['body']
						}
					else:
						return {
							'newupdate': False,
							'unofficial': False,
							'error': False
						}
		except Exception:
			return {
				'newupdate': False,
				'error': True,
				'exceeded': False,
				'nowifi': False
			}

# https://stackoverflow.com/a/24072653
class FocusFrame(tk.Frame):
	def __init__(self, *args, **kwargs):
		tk.Frame.__init__(self, *args, **kwargs)
		self.bind('<1>', lambda event: self.focus_set())

class Address(FocusFrame):
	def __init__(self, master, gui, index, data, **kw):
		tk.Frame.__init__(self, master, **kw)
		self.gui = gui
		self.index = index

		ttk.Label(self, text = 'Address').pack(side = 'left')

		ttk.Button(self, text = 'X', width = 2, command = self.destroy_confirm).pack(side = 'right')
		ttk.Label(self, text = 'H   ').pack(side = 'right')

		vcmd = self.register(self.gui.validate_hex)

		self.pc = ttk.Entry(self, width = 6, justify = 'right', validate = 'key', validatecommand = (vcmd, '%S', '%P', '%d', range(0, 0x10000, 2)))
		if data is not None: self.pc.insert(0, f'{data & 0xfffe:04X}')
		self.pc.bind('<KeyPress>', self.cap_input)
		self.pc.pack(side = 'right')

		ttk.Label(self, text = ':').pack(side = 'right')

		self.csr = ttk.Entry(self, width = 2, justify = 'right', validate = 'key', validatecommand = (vcmd, '%S', '%P', '%d', range(0x10)))
		if data is not None: self.csr.insert(0, f'{(data >> 16) & 0xf:X}')
		self.csr.bind('<KeyPress>', self.cap_input)
		self.csr.pack(side = 'right')

		self.bind('<FocusOut>', self.pad)

	def cap_input(self, event):
		if event.char.lower() in '0123456789abcdef':
			event.widget.insert('end', event.char.upper())
			return 'break'

	def pad(self, event):
		self.pc.insert(0, '0'*(4-len(self.pc.get())))
		if len(self.csr.get()) == 0: self.csr.insert(0, '0')

	def destroy_confirm(self):
		if tk.messagebox.askyesno('Warning', 'Are you sure you want to delete this gadget?', icon = 'warning'): self.destroy()

	def destroy(self):
		del self.gui.gadgets[self.index]
		if len(self.gui.gadgets) == 0: self.gui.clearbutton['state'] = 'disabled'
		super().destroy()

# https://stackoverflow.com/a/65447493
class ThreadWithResult(threading.Thread):
	def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
		if kwargs is None:
			kwargs = {}

		def function(): self.result = target(*args, **kwargs)

		super().__init__(group=group, target=function, name=name, daemon=daemon)

# https://stackoverflow.com/a/16198198
class VerticalScrolledFrame(FocusFrame):
	def __init__(self, parent, *args, **kw):
		tk.Frame.__init__(self, parent, *args, **kw)

		vscrollbar = tk.Scrollbar(self, orient = 'vertical')
		vscrollbar.pack(fill = 'y', side = 'right')
		canvas = tk.Canvas(self, bd = 0, highlightthickness = 0, yscrollcommand = vscrollbar.set)
		canvas.pack(side = 'left', fill = 'both', expand = True)
		vscrollbar.config(command = canvas.yview)

		canvas.xview_moveto(0)
		canvas.yview_moveto(0)

		self.interior = interior = tk.Frame(canvas)
		interior_id = canvas.create_window(0, 0, window = interior, anchor = 'nw')

		def _configure_interior(event):
			size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
			canvas.config(scrollregion = '0 0 %s %s' % size)
			if interior.winfo_reqwidth() != canvas.winfo_width():
				canvas.config(width=interior.winfo_reqwidth())
		interior.bind('<Configure>', _configure_interior)

		def _configure_canvas(event):
			if interior.winfo_reqwidth() != canvas.winfo_width():
				canvas.itemconfigure(interior_id, width=canvas.winfo_width())
		canvas.bind('<Configure>', _configure_canvas)

