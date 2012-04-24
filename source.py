import gtksourceview2

TERMINATORS = set(['*', '>', '<', '=', '%', '+', '-', '*', '/',
		'&', '|', '!', '^', ',', ';', ':', '~', '[', ']', '?',
		'\r', '\n', '\t', ' ', '.', '(', ')', '{', '}'])
CONTINUATORS = set(['::', '.*', '->*', '->', '.'])

class ParserIter:
	def __init__(self, it):
		self.__dict__['it'] = it
	
	def __getattr__(self, name):
		return getattr(self.it, name)
	
	def __setattr__(self, name, value):
		return setattr(self.it, name, value)

	def __len__(self):
		return 0

	def __getitem__(self, key):
		if not isinstance(key, slice):
			raise TypeError
		if key.step is not None:
			raise TypeError
		i = key.start
		j = key.stop
		begin = self.copy()
		if i < 0:
			i = -i
			while i and begin.backward_char():
				i -= 1
		else:
			while i and begin.forward_char():
				i -= 1
		end = self.copy()
		if j < 0:
			j = -j
			while j and end.backward_char():
				j -= 1
		else:
			while j and end.forward_char():
				j -= 1
		return begin.get_slice(end)

def parse_backward(it):
	it = ParserIter(it)
	moving = True
	while moving:
		moving = False
		if it.get_char() not in TERMINATORS:
			while it.backward_char():
				if it.get_char() in TERMINATORS:
					it.forward_char()
					break
			for cont in CONTINUATORS:
				off = len(cont)
				if it[-off:0] == cont:
					it.backward_chars(off+1)
					moving = True
					break
	return it

def parse_forward(it):
	while it.get_char() not in TERMINATORS:
		if not it.forward_char():
			break
	return it

def parse_forward_calls(it):
	while it.get_char() not in TERMINATORS:
		if not it.forward_char():
			break
	if it.get_char() == '(':
		level = 1
		while level and it.forward_char():
			if it.get_char() == '(':
				level += 1
			elif it.get_char() == ')':
				level -= 1
		it.forward_char()
	return it

class Buffer(gtksourceview2.Buffer):
	def cursor_word_forward(self):
		mark = self.get_insert()
		it = self.get_iter_at_mark(mark)
		it.forward_word_end()
		self.place_cursor(it)
	
	def cursor_word_backward(self):
		mark = self.get_insert()
		it = self.get_iter_at_mark(mark)
		it.backward_word_start()
		self.place_cursor(it)
	
	def get_symbol_under_cursor(self):
		mark = self.get_insert()
		begin = parse_backward(self.get_iter_at_mark(mark))
		end = parse_forward(self.get_iter_at_mark(mark))
		symbol = begin.get_slice(end)
		return symbol if symbol else None
	
	def get_call_under_cursor(self):
		mark = self.get_insert()
		begin = self.get_iter_at_mark(mark)
		while begin.get_char() == '(':
			if not begin.backward_char():
				break
		begin = parse_backward(begin)
		end = parse_forward_calls(self.get_iter_at_mark(mark))
		call = begin.get_slice(end)
		return call if call else None
