#! /usr/bin/python

import re
class FoundMatch(Exception):
	pass

class Interpreter():
	def __init__(self, instruction, mode="single", algorithm="random"):
		self.instruction = instruction
		self.algorithm = algorithm
		self.instruction_set = []
		if mode == "file":
			print self._digest_instructions_from_file()

	def _random(self, low, high):
		import random
		return random.randrange(low, high) 

	def _sanitize_str(self, string):
		new_string = ""
		for c in string:
			pattern = re.compile(r'[a-zA-Z0-9_]')
			if pattern.match(c):
				new_string += c.lower().strip()
			elif c == ' ':
				new_string += ' '
			else:
				pass
		return new_string

	def _is_instance_of_load(self, token, load_object, spaces=False):
		if len(load_object[2]) > 1:
			for e_object in load_object[2]:
				if not spaces: #If the token includes no spaces
					if e_object.lower() == token:
						return True
				else:
					if token in e_object.lower():
						return True
		else:
			if not spaces: #If the token includes no spaces
				if load_object[2][0].lower() == token:
					return True
			else:
				if token in load_object[2][0].lower():
					return True
		return False

	def _extract_primatives(self, object):
		primatives = []
		variables = []
		if isinstance(object, list):
			selectable_object = object
			for object in selectable_object:
				try:
					if object[0] == '"' and object[-1] == '"':
						primatives.append(object[1:-1])
					elif object == 'None':
						pass
					else:
						variables.append(object)
				except IndexError:
					return (1, "failed to extract primatives and variables due to a syntax error", str(object))
		else:
						
			if object[0] == '"' and object[-1] == '"':
				primatives.append(object[1:-1])
			elif object == 'None':
				pass
			else:
				variables.append(object)
		return (0, "successfully extracted primatives and variables", (primatives, variables))

	
	def _load(self, name, variable=True):
		results = []
		if variable:
			try:
				if "." in name:
					f = open("objects/" + name.replace(".", "/"))
				else:
					f = open("objects/" + name)
				lines = f.read().strip().split('\n')
				for line in lines:
					results.append(line.strip())
				return (0, "loaded object " + name, results)
		
			except IOError:
				return (-1, "object " + name + " does not exist", None)
		else:
			results.append(name)
			return (0, "loaded primative " + name, results)


	def _digest_instructions_from_file(self):
		try:
			f = open(self.instruction, "r")
		except IOError:
			return (-1, "file not found " + self.instruction, None)
		lines = f.read().strip().split("\n")
		for line in lines:
			if line[0] != "#":
				objects = re.findall(r'\{(.*?)\}', line)				
				if len(objects) > 0:
					i = 0
					response_objects = []
					for object in objects:
						try:
							if i == 0:
								received_object = re.findall(r'\[(.*?)\]', objects[0])
								temp_received_object = []
								for object in received_object:
									e_objects = object.split('|')
									if len(e_objects) > 1:
										temp_received_object.append(e_objects)
									else:
										temp_received_object.append(e_objects[0])
								received_object = temp_received_object
							else:
								try:
									objects[1]
									response_objects.append(object)
								except IndexError:
									return (1, "missing response true logic", None)
							i+=1	
						except IndexError:
							return (1, "missing received logic", None)
				
						self.instruction_set.append( (received_object, response_objects) )
				else:
					return (1, 'invalid syntax - hint {[][]...["foo"|"bar"|object]}{[object]}{None};', None)
		return (0, "loaded " + str(len(lines)) + " instructions successfully", None)
	
	def generate_message(self, instruction):
		load_list = []
		load_objects = []
		result_selection = []
		result = ''
		OR = "|"
		END = ";"
		if instruction[-1] != ";":
			return (1, "must terminate with ;", None)
		objects = re.findall(r'\[(.*?)\]', instruction)				
		for object in objects:
			if OR in object:
				e_objects = object.split(OR)	
				selectable_object = []
				for e_object in e_objects:
					selectable_object.append(e_object.strip())
				load_list.append(selectable_object)
			else:
				load_list.append(object)

		if self.algorithm == "random":
			for object in load_list:
				if isinstance(object, list):
					extracted_object = self._extract_primatives(object)
					primatives = extracted_object[2][0]
					variables = extracted_object[2][1]
					temp_load_objects = []
					try:
						variable_load = self._load(variables[self._random(0, len(variables))])
						if variable_load[0] != -1:
							temp_load_objects.append(variable_load)
						else:
							return variable_load
					except ValueError:
						pass
					try:
						if len(primatives) > 0: 
							primative_load = self._load(primatives[self._random(0, len(primatives))] , variable=False)
							temp_load_objects.append(primative_load)
					except ValueError:
						pass
					load_objects.append(temp_load_objects[self._random(0, len(temp_load_objects))])
				else:
					extracted_object = self._extract_primatives(object)
					try:
						primative = extracted_object[2][0][0]
						primative_load = self._load(primative, variable=False)
						load_objects.append(primative_load)
						
					except IndexError:
						try:
							variable = extracted_object[2][1][0]
						except IndexError:
							variable = "None"
						variable_load = self._load(variable)		
						if variable_load[0] != -1: 
							load_objects.append(variable_load)
						else:
							return variable_load
			#print load_objects
			for object in load_objects:
				result_selection.append(object[2][self._random(0, len(object[2]))])
		symbols = [' ', ',', '!', '?']
		
		j = 0
		for i in instruction:
			if i == "[":
				result += result_selection[j]
				j+=1
			elif i in symbols:
				result = result.strip() + i
			else:
				pass
		return result

	def eval_str(self, string, mode="best_match"):
		sanitized_string = self._sanitize_str(string)
		tokenized_string = sanitized_string.split(' ')
		ranked_responses = []
		print len(self.instruction_set)
		for instruction in self.instruction_set:
			load_objects = []	
			matches = 0
			received_object = instruction[0]
			response_objects = instruction[1]
			response_strings = []
			for response in response_objects:
				response_strings.append(self.generate_message(response))
			#print to_send_string
			received_logic_statement_object = []
			for object in received_object:
				extracted_objects = self._extract_primatives(object)
				primatives = extracted_objects[2][0]
				temp_variables = []
				temp_primatives = []
				for primative in primatives:
					load_objects.append(self._load(primative, variable=False))
					temp_primatives.append(self._load(primative, variable=False))
				variables = extracted_objects[2][1]
				for variable in variables:
					load_objects.append(self._load(variable))
					temp_variables.append(self._load(variable))
				received_logic_statement_object.append( (temp_primatives, temp_variables) )
			for object in received_logic_statement_object:
				print "AND " + str(object)
				
			for object in load_objects:		
				for token in tokenized_string: #looking at individual words
					if token != '':
						if self._is_instance_of_load(token, object):
							matches += 1
				if self._is_instance_of_load(sanitized_string, object, spaces=True): #look for exact phrase
					matches += len(sanitized_string.split(' '))	
			ranked_responses.append( (matches, received_object, response_strings) )
		sorted_ranked_responses = sorted(ranked_responses, key=lambda tup: tup[0])
		sorted_ranked_responses.reverse()
		if mode == "best_match":
			if sorted_ranked_responses[0][0] == 0:
				return None
			return sorted_ranked_responses[0]
		else:
			return sorted_ranked_responses

			
	
#Interpreter("instructions/corie", mode="file")	
#Interpreter(None).generate_message('[greetings.casual_hi|":)"|"0_0"|names.corie];')
