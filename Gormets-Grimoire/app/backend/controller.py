#!/usr/bin/python3

#python imports
import cgi
import cgitb
import sys
import os
import secrets
import logging
from jsonpickle import encode
#flask imports
from flask import Flask
from flask import abort
from flask import request
from flask import render_template
from flask import session
from flask import redirect
from flask import url_for
from flask import render_template
from flask import flash
from flask import jsonify
#model + dao imports
from backend.models.recipe import Recipe
from backend.models.user import User
from backend.models.ingredient import Ingredient
from backend.dao.userdao import UserDao
from backend.dao.recipedao import RecipeDao

#Features:
	#Search for recipes based on ingredients.
	#Add new recipes including ingredients and cooking instructions.
	#favorite favorite recipes in a personal account.
	#Generate a shopping list from selected recipes.

#logging configuration
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)10s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')

@app.route('/', methods=['GET'])
def index():
	log.debug("Accessing the login page")
	return redirect(url_for('login'))

@app.route('/logout')
def logout():
	log.debug('logout(): method called')
	session.pop('userid', None)
	flash('You have been logged out.')
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	if 'submit' in request.form:
		log.debug('Login: submit found')
		action= request.form['submit']
		log.debug(action)
		if action=='Login':
			log.debug('Login: action ==Login')
			userid= request.form['userid']

			password= request.form['password']
			if isValid(userid, password):
				log.debug('LOGIN: login is valid')
				session['userid']= userid
				log.debug('LOGIN: redirecting to home')
				return home()
			else:
				log.debug('LOGIN: loading home page')
				return render_template('home.html', userid=userid)
		elif action=='NewUser':
			log.debug('Login: action==NewUser')
			userid= request.form['userid']
			password= request.form['password']
			confirmPass= request.form['confirmPass']
			log.debug('Login: confirmPass: '+confirmPass)
			if createNewUser(userid, password, confirmPass):
				log.debug('Login: new user created')
				session['userid']= userid
				log.debug('Login: redirected to login')
				return login()
			else:
				log.debug('Login reloaded: invalid new user')
				return render_template('login.html')
	else:
		log.debug('Login reloaded: no submit found')
		return render_template('login.html')


#if its the user's first time loading home
	#give them a popup saying: 
		#"Welcome to Gormet's Grimoire!"
			#"We have given you a couple sample recipes to get you started!"
			#"Tap Next to personalize your account!" + Next button that will go to theme popup
		#"Theme"popup
			#"Which theme would you like to use for your account? If not sure this can always be changed under settings"
			#Button for "Light (default)"
			#button for "Dark"
			#button for previous popup "Welcome!" + button for "Next"
		#"Measures" popup
			#button for "Do not convert"
			#button for "Metric (litre, gram)"
			#button for "US Standard (cups, fl oz)"
			#button for "Imperial (pint, oz)"
			#button for previous popup "Theme" + button for "Next"
		#"You are all set and ready to go, Happy Cooking!"
			#"Dont forget to check out FAQ'S (imbedded link to page) for more info and tips!"	
			#button for previous popup "Measures" + button for "Close"				
@app.route('/home', methods=['GET'])
def home():
	log.debug('home(): method called')

	if 'userid' not in session:
		log.debug('HOME(): Please login to view all recipes.')
		return redirect(url_for('login'))

	# Dao Imports
	userdao=UserDao()
	recipedao = RecipeDao()
	userid = session['userid']
	recipes = recipedao.getAllCookbook()
	user = userdao.selectByUserID(userid)

	return render_template('home.html', recipes=recipes, user=user)

#
# METHOD HANDLING SEARCH RESULTS
#
@app.route('/search_results', methods=['POST', 'GET'])
def search_results():
	log.debug('SEARCH_RESULTS(): method called')
	ingredient = request.form.get('searchInput')
	log.debug("SEARCH_RESULTS(): ingredient: {ingredient}")
	if not ingredient:
		log.debug('SEARCH_RESULTS(): Ingredient field cannot be empty!')
		return redirect(url_for('home'))

	recipedao = RecipeDao()
	search_recipes = recipedao.getRecipesByIngredient(ingredient)
	if not search_recipes:
		log.debug(f'SEARCH_RESULTS(): No recipes found with ingredient {ingredient}.')
		return render_template('search_results.html', recipes=search_recipes, ingredient=ingredient)
	else:
		log.debug(f'SEARCH_RESULTS(): {len(search_recipes)} recipes found for ingredient: {ingredient}')
		return render_template('search_results.html', recipes=search_recipes, ingredient=ingredient)

#
# 	METHOD RETURNING JSON DATA FOR JQUERY AUTOCOMPLETE
#
@app.route('/search_ingredients', methods=['GET'])
def search_ingredients():
	log.debug("SEARCH_INGREDIENTS() METHOD CALLED")
	if 'userid' not in session:
		log.debug('SEARCH_INGREDIENTS(): User not logged in.')
		return jsonify([])  # Return an empty array if not logged in for security

	term = request.args.get('term', '')  # args for GET request handling
	if not term:
		log.debug('SEARCH_INGREDIENTS(): No search term provided.')
		return jsonify([])  #return an empty array if no term provided

	recipedao = RecipeDao()
	ingredients = recipedao.searchIngredients(term)  #method returns a list of unique ingredient names
	return jsonify(ingredients)



@app.route('/addRecipe', methods=['GET', 'POST'])
def addRecipe():
	log.debug('ADD-RECIPE(): method called')
	if 'userid' not in session:
		log.debug('ADD-RECIPE(): Please login to view all recipes.')
		return redirect(url_for('login'))

	#Dao Imports
	recipedao = RecipeDao()
	userdao = UserDao()
	userid = session['userid']

	if request.method == 'POST':
		recipeId = recipedao.getRecipeIDMax()
		title = request.form.get('title')
		description = request.form.get('description')
		ingredients = request.form.get('ingredients')
		instructions = request.form.get('instructions')

		if(description == None):
			log.debug('ADD-RECIPE(): description = "{description}"')
			description = 'This recipe has no description'
		
		if not (title and ingredients and instructions):
			log.debug('ADD-RECIPE(): All fields are required!')
			log.debug('ADD-RECIPE(): title = "{title}"')
			log.debug('ADD-RECIPE(): description = "{description}"')
			log.debug('ADD-RECIPE(): ingredients = "{ingredients}"')
			log.debug('ADD-RECIPE(): instructions = "{instructions}"')
			return redirect(url_for('addRecipe'))

		new_recipe = Recipe(recipeId=recipeId, title=title, description=description, ingredients=ingredients, instructions=instructions)
		recipedao.insertToCookbook(session['userid'], new_recipe)
		log.debug('ADD-RECIPE(): Recipe added successfully with recipeId = {recipeId}')
		log.debug('ADD-RECIPE(): redirecting to MY-RECIPES')
		return redirect(url_for('myRecipes'))
	
	return render_template('addRecipe.html')

@app.route('/userSettings', methods=['GET', 'POST'])
def userSettings():
	log.debug('USER-SETTINGS(): method called')

	#ensure the user is logged in
	if 'userid' not in session:
		log.debug('USER-SETTINGS(): Please login to view user settings.')
		return redirect(url_for('login'))
	
	userdao = UserDao()
	userid = session['userid']
	user = userdao.selectByUserID(userid)
	
	#if the form has been submitted, update the user settings
	if request.method == 'POST':
		#extract the new settings from the form submission
		newPassword = request.form.get('newPassword')
		# Add other settings you allow the user to change, such as email, username, etc.
		
		# update the user object with new settings
		if newPassword:  # make sure the new password is not empty
			user.password = newPassword
			# update other user attributes here
			
		#persist the updated user settings to the database
		userdao.update(user)
		log.debug('USER-SETTINGS: User settings have been updated.')
		# Redirect to home or some confirmation page
		return redirect(url_for('home'))
	
	#if method is GET, display the current settings to the user
	return render_template('userSettings.html', user=user)

@app.route('/myRecipes',  methods=['GET', 'POST'])
def myRecipes():
	log.debug('MY-RECIPES() method called')
	userid= session['userid']
	viewRecipe= None

	#Dao Imports
	recipedao= RecipeDao()
	userdao = UserDao()
	#get user
	user = userdao.selectByUserID(userid)

	if 'userid' not in session:
		log.debug('MY-RECIPES:Please login to view your recipes.')
		return redirect(url_for('login'))
	else:
		recipes = recipedao.getUsersCookbook(userid)
		log.debug(f'Rendering MY-RECIPES with {len(recipes)} recipes and viewRecipe={viewRecipe}')

		if 'action' in request.form:
			action= request.form['action']
			recipeId= request.form['recipeId']
			log.debug(f'MY-RECIPES(): action found -> {action}')
			
			if action== 'delete':
				recipedao.deleteRecipeCookbook(recipes[recipeId])
				log.debug(f'MY-RECIPES: recipeId = {recipeId} deleted.')
				log.debug('MY-RECIPES: reloading')
				return render_template('myRecipes.html', **locals())
			elif action=='view':
				viewRecipe= recipes[recipeId]
				log.debug(f'MY-RECIPES: recipeId = {recipeId} viewed.')
				log.debug('MY-RECIPES: reloading')
				return render_template('myRecipes.html', **locals())
		else:
			log.debug('MY-RECIPES: reloaded')
			return render_template('myRecipes.html', **locals())

@app.route('/favoriteRecipes', methods=['GET', 'POST'])
def favoriteRecipes():
	log.debug('FAVORITE-RECIPES(): method called')
	if 'userid' not in session:
		log.debug('FAVORITE-RECIPES(): User is not logged in.')
		return redirect(url_for('login'))
	else:
		viewRecipe=None
		userid = session['userid']
		#Dao Imports
		recipedao= RecipeDao()
		userdao = UserDao()
		#get favorited recipes from userdao
		recipes = userdao.getFavoritedRecipesForUser(userid)
		user = userdao.selectByUserID(userid)

		log.debug(f'Rendering FAVORITE-RECIPES with {len(recipes)} recipes and viewRecipe={viewRecipe}')

		if 'action' in request.form:
			action= request.form['action']
			log.debug(f'FAVORITE-RECIPES(): action found -> {action}')

			if action=='view':
				viewRecipe= recipes[recipeId]
				log.debug(f'FAVORITE-RECIPES: recipeId = {recipeId} viewed.')
				log.debug('FAVORITE-RECIPES: reloading')
				return render_template('favoriteRecipes.html', **locals())
		else:
			log.debug('FAVORITE-RECIPES: reloaded')
			return render_template('favoriteRecipes.html', **locals())

@app.route('/cart', methods=['GET', 'POST'])
def cart():
	log.debug('CART(): method called')
	if 'userid' not in session:
		log.debug('CART(): User is not logged in.')
		return redirect(url_for('login'))

	userid = session['userid']
	#Dao Imports
	recipedao= RecipeDao()
	userdao = UserDao()
	recipes = []

	user = userdao.selectByUserID(userid)
	#get users cart recipes
	cart = user.cart
	if len(cart)>0:
		recipes = userdao.getCartForUser(user.userid)
		ingredients = recipedao.getIngredientsByRecipe(cart)
		log.debug(f'Rendering CART with {len(recipes)} recipes and {len(ingredients)} ingredients!')
		return render_template('cart.html', recipes=recipes, ingredients=ingredients, user=user)
	else:
		log.debug(f'CART is empty sad face')
		return render_template('cart.html', user=user)

@app.route('/allRecipes',  methods=['GET', 'POST'])
def allRecipes():
	log.debug('ALL-RECIPES(): method called')
	if 'userid' not in session:
		log.debug('ALL-RECIPES():Please login to view all recipes.')
		return redirect(url_for('login'))

	userid= session['userid']
	viewRecipe= None

	#Dao Imports
	recipedao = RecipeDao()
	userdao = UserDao()

	recipes = recipedao.getAllCookbook()
	log.debug(f'Rendering ALL-RECIPES(): with {len(recipes)} recipes and viewRecipe={viewRecipe}')

	if 'action' in request.form:
		action= request.form['action']
		
		log.debug(f'ALL-RECIPES(): action found -> {action}')

		if action=='view':
			viewRecipe= recipes[recipeId]
			log.debug(f'ALL-RECIPES: recipeId = {recipeId} viewed.')
			log.debug('ALL-RECIPES: reloading')
			return render_template('allRecipes.html', **locals())
	else:
		log.debug('ALL-RECIPES: reloaded')
		return render_template('allRecipes.html', **locals())

@app.route('/favoriteRecipe/<int:recipeId>', methods=['POST'])
def favoriteRecipe(recipeId):
	log.debug('FAVORITE-RECIPE() method called')
	if 'userid' not in session:
		log.debug('FAVORITE-RECIPE(): User is not logged in.')
		return redirect(url_for('login'))

	userid = session['userid']
	userdao = UserDao()
	recipedao = RecipeDao()
	# Check if the recipe exists before trying to favorite it
	if not recipedao.selectByRecipeID(recipeId):
		log.debug(f'UNFAVORITE-RECIPE(): Recipe with ID {recipeId} does not exist.')
		return 'UNFAVORITE-RECIPE(): Recipe not found', 404  
	try:
		userdao.favoriteRecipeForUser(userid, recipeId)
		log.debug(f'UNFAVORITE-RECIPE(): Recipe with ID {recipeId} removed from favorited for user {userid}.')
		# might want to return a success message or redirect
		return redirect(url_for('favoriteRecipes'))
	except Exception as e:
		log.error(f'FAVORITE-RECIPE(): Error saving recipe for user: {e}')
		return 'FAVORITE-RECIPE(): An error occurred', 500

@app.route('/unFavoriteRecipe/<int:recipeId>', methods=['POST'])
def unFavoriteRecipe(recipeId):
	log.debug('UNFAVORITE-RECIPE() method called')
	if 'userid' not in session:
		log.debug('UNFAVORITE-RECIPE(): User is not logged in.')
		return redirect(url_for('login'))

	userid = session['userid']
	userdao = UserDao()
	recipedao = RecipeDao()
	# Check if the recipe exists before trying to favorite it
	if not recipedao.selectByRecipeID(recipeId):
		log.debug(f'UNFAVORITE-RECIPE(): Recipe with ID {recipeId} does not exist.')
		return 'UNFAVORITE-RECIPE(): Recipe not found', 404  
	try:
		userdao.removeFavoritedRecipeForUser(userid, recipeId)
		log.debug(f'UNFAVORITE-RECIPE(): Recipe with ID {recipeId} favorited for user {userid}.')

		return redirect(url_for('favoriteRecipes'))
	except Exception as e:
		log.error(f'UNFAVORITE-RECIPE(): Error saving recipe for user: {e}')
		return 'UNFAVORITE-RECIPE(): An error occurred', 500

@app.route('/addCart/<int:recipeId>', methods=['POST'])
def addCart(recipeId):
	log.debug('ADD-CART() method called')
	if 'userid' not in session:
		log.debug('ADD-CART(): User is not logged in.')
		return redirect(url_for('login'))

	userid = session['userid']
	userdao = UserDao()
	recipedao = RecipeDao()
	# Check if the recipe exists before trying to ADD TO CART
	if not recipedao.selectByRecipeID(recipeId):
		log.debug(f'ADD-CART(): Recipe with ID {recipeId} does not exist.')
		return 'ADD-CART(): Recipe not found', 404  
	try:
		userdao.addCartForUser(userid, recipeId)
		log.debug(f'ADD-CART(): Recipe with ID {recipeId} added to cart for user {userid}.')
		# might want to return a success message or redirect
		return redirect(url_for('cart'))
	except Exception as e:
		log.error(f'ADD-CART(): Error saving recipe for user: {e}')
		return 'ADD-CART(): An error occurred', 500

@app.route('/removeCart/<int:recipeId>', methods=['POST'])
def removeCart(recipeId):
	log.debug('REMOVE-CART() method called')
	if 'userid' not in session:
		log.debug('REMOVE-CART(): User is not logged in.')
		return redirect(url_for('login'))

	userid = session['userid']
	userdao = UserDao()
	recipedao = RecipeDao()


	# Check if the recipe exists before trying to REMOVE it
	if not recipedao.selectByRecipeID(recipeId):
		log.debug(f'REMOVE-CART(): Recipe with ID {recipeId} does not exist.')
		return 'REMOVE-CART(): Recipe not found', 404  
	try:
		userdao.removeCartForUser(userid, recipeId)
		log.debug(f'REMOVE-CART(): Recipe with ID {recipeId} removed from cart for user: {userid}.')

		return redirect(url_for('cart'))
	except Exception as e:
		log.error(f'REMOVE-CART(): Error saving recipe for user: {e}')
		return 'REMOVE-CART(): An error occurred', 500

@app.route('/deleteRecipe/<int:recipeId>', methods=['POST'])
def deleteRecipe(recipeId):
	log.debug('DELETE-RECIPE() method called')
	userdao = UserDao()
	recipedao = RecipeDao()
	userid=session['userid']
	user = userdao.selectByUserID(userid)

	if recipeId in user.cart:
		userdao.removeCartForUser(userid, recipeId)

	if recipeId in user.favoritedRecipes:
		userdao.removeFavoritedRecipeForUser(userid, recipeId)

	# Check if the recipe exists before trying to REMOVE it
	if not recipedao.selectByRecipeID(recipeId):
		log.debug(f'DELETE-RECIPE(): Recipe with ID {recipeId} does not exist.')
		return 'DELETE-RECIPE(): Recipe not found', 404  
	try:
		recipedao.deleteRecipeCookbook(recipeId)
		recipedao.deleteRecipeIngredients(recipeId)
		log.debug(f'DELETE-RECIPE(): Recipe with ID {recipeId} deleted from cookbook.')

		return redirect(url_for('myRecipes'))
	except Exception as e:
		log.error(f'DELETE-RECIPE(): Error deleting recipe for user: {e}')
		return 'DELETE-RECIPE(): An error occurred', 500

def validInput(input):
	if input is None or input == '':
		return False
	else:
		return True
#returns true if (useridPassed==user) AND if (userid.pass=passwordPassed)
def isValid(userid, password):
	if userid is None:
		return False
	userdao= UserDao()
	user= userdao.selectByUserID(userid)
	return (user is not None) and (user.password == password)
def createNewUser(userid, password, confirmPass):
	#Dao Import
	userdao = UserDao()
	#make sure User object does not already exist
	existing_user = userdao.selectByUserID(userid)

	if existing_user is None and password == confirmPass:
		favoritedRecipes=[]
		cart=[]
		user = User(userid, password, favoritedRecipes, cart)
		log.debug(f'CREATE-NEW-USER(): New user created! userid= {userid}, password= {password}, num of favoritedRecipes = {len(favoritedRecipes)}, length of cart = {len(cart)}')
		userdao.insert(user)
		return True
	else:
		if existing_user is not None:
			log.debug(f'CREATE-NEW-USER(): Username "{userid}" already exists.')
		elif password != confirmPass:
			log.debug(f'CREATE-NEW-USER(): Passwords: "{password}" and "{confirmPass}" do not match.')
		return False