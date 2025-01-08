import dataset
import logging
from backend.models.recipe import Recipe
from backend.models.ingredient import Ingredient

#logging configuration
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)10s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

class RecipeDao:
	def __init__(self):
		# Connect to the SQLite database
		self.db = dataset.connect('sqlite:///recipes.db')
		# Set table for the cookbook
		self.cookbook = self.db['cookbook'] #primary key = recipeId
		self.ingredients_table = self.db['ingredients'] # primary key = recipeId
		log.debug("RecipeDao initialized with database connection")
	
	def populate(self):
		#list of initial recipes to populate
		initial_recipes = [
			Recipe(0, 'Fried Dough', 'Dough tossed into a frier covered with powdered sugar.', 'Dough, Powdered Sugar', 'Take dough and form into a lumpy pancake. Toss into the fryer for 2-3 minutes or until golden brown. Brush butter onto the hot dough and cover in powdered sugar.'), 
			Recipe(1, 'Salsa', 'Easy Homemade Salsa!', 'Tomatoes, Onion, Garlic, Peppers, Cilantro, Lime', 'Simply throw tomatoes, onion, garlic, peppers, and cilantro into a blender or food processor. Pulse everything until chopped, and then season with salt, pepper and lime. Easy!'),
			Recipe(2, 'Stuffed Peppers', 'Bell peppers are strong enough to hold their shape in the oven, and the flavor is subtle enough to go well with just about anything. This is our favorite recipe, but the customization options are endless', 'white rice, extra-virgin olive oil, medium yellow onion, garlic cloves, tomato paste, ground beef, canned diced tomatoes, dried oregano, Kosher salt, Freshly ground black pepper, bell peppers, shredded Monterey jack, Chopped fresh parsley', 'Preheat oven to 400°. In a small saucepan, prepare rice according to package instructions. Meanwhile, in a large skillet over medium heat, heat oil. Cook onion, stirring occasionally, until softened, about 7 minutes. Stir in garlic and tomato paste and cook, stirring, until fragrant, about 1 minute more. Add ground beef and cook, breaking up meat with a wooden spoon, until no longer pink, about 6 minutes. Drain excess fat. Stir in rice and diced tomatoes; season with oregano, salt, and pepper. Let simmer, stirring occasionally, until liquid has reduced slightly, about 5 minutes. Arrange peppers cut side up in a 13"x9" baking dish and drizzle with oil. Spoon beef mixture into each pepper. Top with cheese, then cover baking dish with foil. Bake peppers until tender, about 35 minutes. Uncover and continue to bake until cheese is bubbly, about 10 minutes more. Top with parsley before serving')
		]
		for recipe in initial_recipes:
			if not self.recipeExists(recipe.recipeId):
				userid = 'admin'
				self.insertToCookbook(userid, recipe)
				log.debug(f"Inserted new recipe: {recipe.recipeId}")

	def recipeToRow(self, userid, recipe):
		# Converts a Recipe object to a dictionary for database insertion
		log.debug(f"Converting recipe {recipe.title} to database row")
		row = dict(user=userid, recipeId=recipe.recipeId, title=recipe.title, description=recipe.description, ingredients=recipe.ingredients, instructions=recipe.instructions)
		return row

	# Converts a database row back to a Recipe and Ingredient object
	def rowToRecipe(self, row):
		log.debug(f"Converting database row to Recipe object for recipe ID {row['recipeId']}")
		return Recipe(row['recipeId'], row['title'], row['description'], row['ingredients'], row['instructions'])

	def rowToIngredient(self, row):
		log.debug(f"Converting database row to Ingredient object for recipe ID {row['recipeId']}")
		return Ingredient(row['recipeId'], row['ingredient'])
	
	#checks if recipe exists
	def recipeExists(self, recipeId):
		exists = self.cookbook.find_one(recipeId=recipeId) is not None
		log.debug(f"Recipe {recipeId} exists: {exists}")
		return exists
	
	def getRecipeIDMax(self):
		rows = self.cookbook.all()  
		id = 0
		for row in rows:
			id = row['recipeId']
		return id+1

	def insertToCookbook(self, userid, recipe):
		#for new recipes, turn their ingredients into ingredient objects
		#attatch recipe id to ingredient objects
		#add to database of ingredients
		log.debug(f"Adding recipe {recipe.title}")
		recipe_row = self.recipeToRow(userid, recipe)
		self.cookbook.insert(recipe_row)
		self.db.commit()
		# Now handle the ingredients
		self.insertIngredients(recipe.recipeId, recipe.ingredients)

	def insertIngredients(self, recipeId, ingredients):
		# Split the ingredients by commas and insert each one into the ingredients table
		log.debug(f"Inserting ingredients for recipe ID {recipeId}")
		ingredient_list = ingredients.split(',')
		for ingredient in ingredient_list:
			ingredient = ingredient.strip()
			if ingredient:  # Ensure no empty strings are inserted
				self.ingredients_table.insert(dict(recipeId=recipeId, ingredient=ingredient))
		self.db.commit()
	
	def selectByRecipeID(self, recipeId):
		row = self.cookbook.find_one(recipeId=recipeId)
		if row:
			log.debug(f"Selected recipe {recipeId}")
			return self.rowToRecipe(row)
		else:
			log.error(f"recipe {recipe} not found in database")
			return None

	def searchIngredients(self, ingredient):
		#search from the ingredients table
		log.debug(f"Searching for ingredient matching: {ingredient}")
		result = []
		rows = self.ingredients_table.find(ingredient={'like': f'%{ingredient}%'})
		for row in rows:
			result.append(row['ingredient'])
		return list(set(result))  # Return unique ingredients only

	def getCookbookIngredients(self):
		result = []
		rows = self.ingredients_table.all()
		for row in rows:
			result.append(self.rowToIngredient(row))
		return result
	
	def getRecipesByIngredient(self, ingredient):
		log.debug(f"getRecipesByIngredient(): Retrieving recipes for ingredient: {ingredient}")
		recipes = []

		# Find all ingredient entries that match the search term
		ingredient_entries = self.ingredients_table.find(ingredient={'like': f'%{ingredient}%'})
		
		# Extract unique recipe IDs from these entries
		recipe_ids = set([entry['recipeId'] for entry in ingredient_entries])

		# Retrieve recipes based on these IDs
		for recipe_id in recipe_ids:
			recipe = self.selectByRecipeID(recipe_id)
			if recipe:
				recipes.append(recipe)
		
		log.debug(f"getRecipesByIngredient(): Found {len(recipes)} recipes containing the ingredient '{ingredient}'")
		return recipes

	
	def getIngredientsByRecipe(self, cart):
		log.debug(f"Retrieving ingredients for recipe ID's in cart: {cart}")
		ingredients = []
		for recipeId in cart:
			temp = []
			rows = self.ingredients_table.find(recipeId=recipeId)
			for row in rows:
				temp.append(row['ingredient'])
			ingredients = temp
		return ingredients


	def getUsersCookbook(self, userid):#maybe put this in userdao and call it on launch
		# Retrieves all recipes associated with a specific user
		result = []
		rows = self.cookbook.find(user=userid)
		for row in rows:
			result.append(self.rowToRecipe(row))
		return result

	def getAllCookbook(self):
		# Retrieves all recipes in the cookbook
		log.debug("Retrieving all recipes from the cookbook")
		result = []
		rows = self.cookbook.all()
		for row in rows:
			result.append(self.rowToRecipe(row))
		return result

	def deleteRecipeCookbook(self, recipeId):
		# Deletes a recipe from the cookbook based on id
		log.debug(f"Deleting recipe with ID {recipeId}")
		self.cookbook.delete(recipeId=recipeId)
		self.db.commit()

	def deleteRecipeIngredients(self, recipeId):
		# Deletes a recipe from the cookbook based on id
		log.debug(f"Deleting recipe ingredients with ID {recipeId}")
		self.ingredients_table.delete(recipeId=recipeId)
		self.db.commit()

	def deleteAllRecipes(self):
		# Deletes all recipes from the cookbook
		log.debug("Deleting all recipes from the cookbook")
		self.cookbook.drop()
dao = RecipeDao()
dao.populate()