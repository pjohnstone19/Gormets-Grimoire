#!/usr/bin/python3

class Recipe:
	def __init__(self, recipeId, title, description, ingredients, instructions):
		self.recipeId = recipeId
		self.title = title
		self.description = description
		self.ingredients = ingredients
		self.instructions = instructions

	def __eq__(self, other):
		if isinstance(other, Recipe):
			return (self.recipeId == other.recipeId and self.title ==other.title and self.description==other.description and self.ingredients == other.ingredients and self.instructions == other.instructions)
		return False