import dataset
import logging
import json
from backend.models.user import User
from backend.models.recipe import Recipe
from backend.dao.recipedao import RecipeDao

# Logging configuration
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

class UserDao:
	def __init__(self):
		self.db = dataset.connect('sqlite:///users.db')
		self.table = self.db['users']
		log.debug("UserDao initialized with database connection")

	def populate(self):
		initial_users = [
			User('admin', '123', favoritedRecipes=[], cart=[]),
			User('support', '123', favoritedRecipes=[], cart=[]),
			User('bob', 'csrocks55', favoritedRecipes=[], cart=[]),
			User('shai', 'csrocks55', favoritedRecipes=[], cart=[]),
			User('sam', 'csrocks55', favoritedRecipes=[], cart=[]),
			User('janet', 'csrocks55', favoritedRecipes=[], cart=[]),
			User('peter', 'lethimcook', favoritedRecipes=[], cart=[])
		]
		for user in initial_users:
			if not self.userExists(user.userid):
				self.table.insert(self.userToRow(user))
				log.debug(f"Inserted new user: {user.userid}")

	def userToRow(self, user):
		favorited_recipes_serialized = json.dumps(user.favoritedRecipes)
		cart_serialized = json.dumps(user.cart)
		log.debug(f"Serialized user {user.userid} for database insertion")
		return {'userid': user.userid, 'password': user.password, 'favoritedRecipes': favorited_recipes_serialized, 'cart': cart_serialized}

	def rowToUser(self, row):
		favorited_recipes = json.loads(row['favoritedRecipes']) if row['favoritedRecipes'] else []
		cart = json.loads(row['cart']) if row['cart'] else []
		log.debug(f"Deserialized database row for user {row['userid']}")
		return User(row['userid'], row['password'], favorited_recipes, cart)

	def userExists(self, userid):
		exists = self.table.find_one(userid=userid) is not None
		log.debug(f"User {userid} exists: {exists}")
		return exists

	def selectByUserID(self, userid):
		row = self.table.find_one(userid=userid)
		if row:
			log.debug(f"Selected user {userid}")
			return self.rowToUser(row)
		else:
			log.error(f"User {userid} not found in database")
			return None

	def update(self, user):
		self.table.update(self.userToRow(user), ['userid'])
		log.debug(f"Updated user {user.userid}")
	
	def insert(self, user):
		self.table.insert(self.userToRow(user))
		self.db.commit()

	def delete(self, userid):
		self.table.delete(userid=userid)
		self.db.commit()
		log.debug(f"Deleted user {userid}")

	def deleteAllUsers(self):
		self.table.drop()
		log.debug("Deleted all users from database")

	def favoriteRecipeForUser(self, userid, recipeId):
		user = self.selectByUserID(userid)
		if user:
			if recipeId not in user.favoritedRecipes:
				user.favoritedRecipes.append(recipeId)
				self.update(user)
				log.debug(f"Added recipe {recipeId} to favorites for user {userid}")
		else:
			log.error(f"User {userid} not found when trying to favorite recipe {recipeId}.")

	def removeFavoritedRecipeForUser(self, userid, recipeId):
		user = self.selectByUserID(userid)
		if user:
			if recipeId in user.favoritedRecipes:
				user.favoritedRecipes.remove(recipeId)
				self.update(user)
				log.debug(f"Removed recipe {recipeId} from favorites for user {userid}")
		else:
			log.error(f"User {userid} not found when trying to remove recipe {recipeId}.")

	def addCartForUser(self, userid, recipeId):
		user = self.selectByUserID(userid)
		if user:
			if recipeId not in user.cart:
				user.cart.append(recipeId)
				self.update(user)
				log.debug(f"Added recipe {recipeId} to cart for user {userid}")
		else:
			log.error(f"User {userid} not found when trying to add recipe {recipeId} to cart.")

	def removeCartForUser(self, userid, recipeId):
		user = self.selectByUserID(userid)
		if user:
			if recipeId in user.cart:
				user.cart.remove(recipeId)
				self.update(user)
				log.debug(f"Removed recipe {recipeId} from cart for user {userid}")
		else:
			log.error(f"User {userid} not found when trying to remove recipe {recipeId} from cart.")

	def getFavoritedRecipesForUser(self, userid):
		user = self.selectByUserID(userid)
		recipedao = RecipeDao()
		if user:
			recipes = [recipedao.selectByRecipeID(rid) for rid in user.favoritedRecipes]
			log.debug(f"Retrieved favorited recipes for user {userid}")
			return recipes
		else:
			log.error(f"User {userid} not found when retrieving favorited recipes")
			return []

	def getCartForUser(self, userid):
		user = self.selectByUserID(userid)
		recipedao = RecipeDao()
		if user:
			recipes = [recipedao.selectByRecipeID(recipeId) for recipeId in user.cart]
			log.debug(f"Retrieved cart items for user {userid}")
			return recipes
		else:
			log.error(f"User {userid} not found when retrieving cart items")
			return []

dao = UserDao()
dao.populate()