import curses
import time
import threading
from random import choice
from words import english_words

DISPLAY_WIDTH = 60
DISPLAY_HEIGHT = 5

TEXTBAR_OFFSET = DISPLAY_HEIGHT
TEXTBAR_HEIGHT = 3
TEXTBAR_WIDTH = DISPLAY_WIDTH

ENDSCREEN_WIDTH = 30
ENDSCREEN_OFFSET_X = 15
ENDSCREEN_OFFSET_Y = 1
ENDSCREEN_HEIGHT = 6
TIMER_LENGTH = 60

class Word(str):
	def __init__(self, instr):
		str.__init__(self)
		self.wrong = False
		self.correct = False
		self.current = False
		self.first_on_line = False
		self.x = 0
		self.y = 0
	
	def get_effect(self):
		if self.current:
			if self.wrong:
				return curses.A_STANDOUT
			else:
				return curses.A_UNDERLINE
		if self.wrong:
			return curses.A_DIM
		if self.correct:
			return curses.A_BOLD
		else:
			return 0
	
class Screen:
	""" Wrapper for display and textbar"""
	def __init__(self):
			
		#Display Init
		self.display = curses.newwin(DISPLAY_HEIGHT+1, DISPLAY_WIDTH, 0, 0)
		self.display.addstr(0,0, "-"*DISPLAY_WIDTH)
		self.display.addstr(DISPLAY_HEIGHT-1,0, "-"*DISPLAY_WIDTH)
		self.display.refresh()
		
		#Textbar Init
		self.textbar = curses.newwin(TEXTBAR_HEIGHT, TEXTBAR_WIDTH, TEXTBAR_OFFSET, 0)
		self.textbar_word = ""
		self.textbar_start = "> "
		self.textbar_end = " <"
		self.textbar.keypad(1)
		
		self.correct_words = []
		self.wrong_words = []
		
		#Ending screen Init
		self.endscreen = curses.newwin(ENDSCREEN_HEIGHT, ENDSCREEN_WIDTH, ENDSCREEN_OFFSET_Y, ENDSCREEN_OFFSET_X)
		self.endscreen.addstr(0,0,'='*ENDSCREEN_WIDTH)
		for row in range(1,ENDSCREEN_HEIGHT-2):
			self.endscreen.addstr(row,0,'|')
			self.endscreen.addstr(row,ENDSCREEN_WIDTH-1,'|')
		self.endscreen.addstr(ENDSCREEN_HEIGHT-2,0,'='*ENDSCREEN_WIDTH)
		
		#Vars
		self.word_index = 0
		self.word_list = []
		self.timer =  Timer(1, self.timer_tick, TIMER_LENGTH, self.timer_finish, self)
		self.time_str = "1:00"
		self.textbar_cleared = self.textbar_start + ' '*(TEXTBAR_WIDTH-len(self.textbar_start)-len(self.textbar_end)-len(self.time_str)-1) + self.textbar_end + " " + self.time_str
		self.time_str_x = TEXTBAR_WIDTH-len(self.time_str)
		self.is_over = False
		self.is_started = False
		self.clear_textbar()
		
		self.add_n_words(DISPLAY_WIDTH*(DISPLAY_HEIGHT-2))
		self.word_list[0].current = True
		
		self.display_list()
		self.textbar.move(0,len(self.textbar_start))
	
	def timer_tick(self, elapsed):
		self.time_str = self.format_time(elapsed)
		loc = self.textbar.getyx()
		self.textbar.addstr(0, self.time_str_x, self.time_str)
		self.textbar.move(loc[0], loc[1])
		self.textbar_cleared = self.textbar_cleared[:-len(self.time_str)] + self.time_str
		self.textbar.refresh()
		
	def timer_finish(self):
		self.is_over = True
		self.time_str = "0:00"
		loc = self.textbar.getyx()
		self.textbar.addstr(0, self.time_str_x, self.time_str)
		self.textbar.move(loc[0], loc[1])
		self.textbar_cleared = self.textbar_cleared[:-len(self.time_str)] + self.time_str
		self.textbar.refresh()
		self.update_endscreen()
		self.endscreen.refresh()
	
	def update_endscreen(self):
		#including spaces like online
		correct_keystrokes = self.get_list_length(self.correct_words)
		wrong_keystrokes = self.get_list_length(self.wrong_words)
		
		wpm_str = "WPM: {}".format(int(round(correct_keystrokes/5.0)))
		wpm_loc = ENDSCREEN_WIDTH/4 - len(wpm_str)/2 + 1
		
		total_strokes = correct_keystrokes + wrong_keystrokes 
		if total_strokes > 0:
			acc_str = "ACC: %{}".format(round(float(100*correct_keystrokes)/(total_strokes),1))
		else:
			acc_str = "ACC: %0.0"
		acc_loc = 3*ENDSCREEN_WIDTH/4 - len(acc_str)/2 - 1
		
		words_str = "W: ({}|{})".format(len(self.correct_words), len(self.wrong_words))
		words_loc = ENDSCREEN_WIDTH/4 - len(words_str)/2 + 1
		
		keys_str = "K: ({}|{})".format(correct_keystrokes, wrong_keystrokes)
		keys_loc = 3*ENDSCREEN_WIDTH/4 - len(keys_str)/2 - 1
		
		self.endscreen.addstr(1, wpm_loc if wpm_loc > 0 else 0, wpm_str)
		self.endscreen.addstr(1, acc_loc if acc_loc < ENDSCREEN_WIDTH else ENDSCREEN_WIDTH-1, acc_str)
		self.endscreen.addstr(2, words_loc if words_loc > 0 else 0, words_str)
		self.endscreen.addstr(2, keys_loc if keys_loc < ENDSCREEN_WIDTH else ENDSCREEN_WIDTH-1, keys_str)
		
		enter_message = "press enter to restart..."
		self.endscreen.addstr(3, ENDSCREEN_WIDTH/2 - len(enter_message)/2, enter_message)
		
	
	def format_time(self, elapsed):
		time_left = TIMER_LENGTH - int(round(elapsed))
		if time_left >= 60:
			return "1:00"
		return "0:%02d" % (time_left,)
	
	def start_timer(self):
		self.timer.start()
	
	def add_n_words(self, n):
		for _ in range(n):
			self.word_list.append(Word(choice(english_words)))
			
	def get_list_length_no_spaces(self, inlist):
		length = 0
		for word in inlist:
			length += len(word.strip())
		return length
	
	def get_list_length(self, inlist):
		length = 0
		for word in inlist:
			length += len(word) + 1
		return length - 1 if length != 0 else 0
	
	def update_word(self, word):
		self.display.chgat(word.y, word.x, len(word), word.get_effect())
	
	def display_list(self):
		line_length = 0
		line = 1
		for index, word in enumerate(self.word_list):
			newstr = " {}".format(word)
			if line_length + len(newstr) < DISPLAY_WIDTH:
				self.display.addstr(line, line_length, newstr, word.get_effect())
				self.display.chgat(line, line_length, 1, 0)
			else:
				#add remainder spaces
				self.display.addstr(line, line_length, (DISPLAY_WIDTH-line_length)*' ')
				line_length = 0
				line += 1
				if (line > DISPLAY_HEIGHT-2):
					self.display.refresh()
					return
				else:
					self.display.addstr(line, line_length, newstr, word.get_effect())
					word.first_on_line = True
			word.x = line_length+1
			word.y = line
			line_length += len(newstr)
		self.display.refresh()
		
	def restart(self):
		self.__init__()
	
	def move_up(self, first_index):
		self.word_list = self.word_list[first_index:]
		self.word_index -= first_index
		if self.get_list_length(self.word_list) <= DISPLAY_WIDTH*(DISPLAY_HEIGHT-2):
			# of course this is on average 5 times more words than we need
			self.add_n_words(DISPLAY_WIDTH)
		
	
	def getch(self):
		return self.textbar.getch()
		
	def on_word_complete(self):
		word = self.word_list[self.word_index]
		word.current = False
		if (self.textbar_word == word):
			word.wrong = False
			word.correct = True
			self.correct_words.append(word)
		else:
			word.wrong = True
			word.correct = False
			self.wrong_words.append(word)
		self.word_index+=1
		self.word_list[self.word_index].current = True
		self.clear_textbar()
		if self.word_list[self.word_index].first_on_line:
			self.move_up(self.word_index)	
		self.display_list()
	
	def is_start_wrong(self, start_word):
		word = self.word_list[self.word_index]
		if len(start_word) > len(word):
			return True
		for i in range(len(start_word)):
			if word[i] != start_word[i]:
				return True
		return False
	
	def update_right_wrong(self):
		self.word_list[self.word_index].wrong = self.is_start_wrong(self.textbar_word)
		self.word_list[self.word_index].correct = not self.word_list[self.word_index].wrong
		self.update_word(self.word_list[self.word_index])
		self.display.refresh()
	
	def on_char(self, c):
		loc = self.textbar.getyx()
		#print(c, curses.keyname(c))
		if not self.is_over:
			if (c == curses.KEY_DC or c == curses.KEY_BACKSPACE or c == 127):
				if (loc[1] >= len(self.textbar_start)):
					self.textbar_word = self.textbar_word[:-1]
					self.textbar.addch(loc[0], loc[1], ' ') 
					self.textbar.move(loc[0], loc[1])
				else:
					self.textbar.move(loc[0], loc[1]+1)
				self.update_right_wrong()
			elif (c == 32):
				if self.textbar_word != "":
					self.on_word_complete()
				else:
					self.textbar.move(loc[0], len(self.textbar_start))
			elif (c == 10):
				if self.textbar_word != "":
					self.on_word_complete()
				else:
					self.textbar.move(0, len(self.textbar_start))
			else:
				#normal char
				if not self.is_started:
					self.start_timer()
					self.is_started = True
				self.textbar_word += chr(c)
				self.update_right_wrong()
		else:
			if (c == 10):
				self.restart()
			elif (c == curses.KEY_DC or c == curses.KEY_BACKSPACE or c == 127):
				self.textbar.move(loc[0], loc[1]+1)
			elif (c == 32):
				self.textbar.move(loc[0], loc[1]-1)
			else:
				self.textbar.addch(loc[0], loc[1]-1, ' ') 
				self.textbar.move(loc[0], loc[1]-1)
	
	def clear_textbar(self):
		self.textbar_word = ""
		self.textbar.addstr(0,0, self.textbar_cleared)
		self.textbar.move(0,len(self.textbar_start))
		self.textbar.refresh()
	
	def refresh(self):
		self.textbar.refresh()

class Timer:
	def __init__(self, interval_time, interval_callback, final_time, final_callback, screen_ref):
		self.main_thread = threading.Thread(target=self.tick)
		self.interval_callback = interval_callback
		self.interval_time = interval_time
		self.final_time = final_time
		self.screen_ref = screen_ref
		self.final_callback = final_callback
		
	def start(self):
		self.main_thread.start()
		
	def tick(self):
		start_time = time.time()
		interval_tick = start_time
		while True:
			inner_time = time.time()
			if inner_time - interval_tick >= self.interval_time:
				interval_tick = inner_time
				self.interval_callback(inner_time-start_time)
			elif inner_time - start_time >= self.final_time:
				self.final_callback()
				return
			time.sleep(0.1)
			
		
		
		
def main(stdscr):
	screen = Screen()
	curses.echo()
	while True:
		screen.on_char(screen.getch())
		screen.refresh()
	
if __name__ == "__main__":
	curses.wrapper(main)