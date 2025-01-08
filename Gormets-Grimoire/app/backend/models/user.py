#!/usr/bin/python3

class User:
	def __init__(self, userid, password, favoritedRecipes, cart):
		self.userid = userid
		self.password = password
		self.favoritedRecipes = [] or favoritedRecipes# initialize empty list 
		self.cart = [] or cart# initialize empty list 

	def __str__(self):
		return f"{self.userid} {self.password}"
