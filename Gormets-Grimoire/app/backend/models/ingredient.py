#!/usr/bin/python3

class Ingredient:
	def __init__(self, recipeId, ingredient):
		self.recipeId = recipeId
		self.ingredient = ingredient

	def __str__(self):
		return f"{self.recipeId} {self.ingredient}"
