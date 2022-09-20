from discord.ext.commands import Bot
import discord
import arrapi
import requests
from discord_components import DiscordComponents, Button, ComponentsBot, ButtonStyle, ActionRow
import random
import os
from dotenv import load_dotenv 
load_dotenv()

#Radarr url and api key
radarUrl = os.getenv("RADARRURL")
radarApiKey = os.getenv("RADARRAPIKEY")
radarr = arrapi.RadarrAPI(radarUrl, radarApiKey)

#Sonarr url and api key
sonarrUrl = os.getenv("SONARRURL")
sonarrApiKey = os.getenv("SONARRAPIKEY")
sonarr = arrapi.SonarrAPI(sonarrUrl, sonarrApiKey)

#Initialize discord bot token to be used with
client = discord.Client()
TOKEN = os.getenv("TOKEN")

tmdbapi = os.getenv("TMDBAPI")

bot = ComponentsBot(command_prefix = "!")

#Function to add movie to plex
@bot.command()
async def movie(ctx, *, arg):
    #Movie to search
    user_message =  str(arg) 

    #TMDB api
    response = requests.get("https://api.themoviedb.org/3/search/movie?api_key=" + tmdbapi + "&language=en-US&query=" + user_message)
    data = response.json()
    
    #List variable for movie results
    list = data['results']
    
    message = await ctx.message.channel.send('Search Query:')
    listcount = 0

    #
    for thing in list:
        listcount += 1
        title = str(thing['original_title'])
        description = str(thing['overview'])
        poster = str("https://image.tmdb.org/t/p/w500" + thing['poster_path'])
        movid = thing['id']
        movurl = str("https://www.themoviedb.org/movie/" + str(movid))

        addButton = Button(label="Add", style=ButtonStyle.green,  custom_id='add')
        nextButton = Button(label="Next", style=ButtonStyle.red, custom_id='next')
        actionRow = ActionRow(addButton, nextButton)

        color = discord.Color.from_rgb(random.randint(0,255), random.randint(0,255), random.randint(0,255))

        embed=discord.Embed(
            title = title, 
            url = movurl, 
            description = description, 
            color = color).set_image(url = poster)
        embeded = await ctx.message.channel.send(embed=embed, components = [actionRow])

        interaction = await bot.wait_for(
            "button_click", check = lambda i: i.custom_id in ["add", "next"]
        )

        if interaction.custom_id == "add":
            try:
                movie = radarr.get_movie(tmdb_id=movid)
                movie.add("/movies", "HD-1080p", "English")
                await embeded.delete()
                await message.delete()
                await ctx.message.channel.send(embed=embed)
                await ctx.message.channel.send(title + ' had been added to Radarr and will be searched for.')
            except arrapi.exceptions.Exists:
                await embeded.delete()
                await message.delete()
                await ctx.message.channel.send(embed=embed)
                await ctx.message.channel.send('That movie already exists!')
                
            break
        else:
            await embeded.delete()
        
        if listcount == 5:
            await message.delete()
            await ctx.message.channel.send('`End of query`')
            break
    return


#!tv command
@bot.command()
async def tv(ctx, *, arg):
    #Set user_message equal input
    try:
        user_message =  str(arg)
    except discord.ext.commands.errors.MissingRequiredArgument:
        await ctx.message.channel.send('Please add an argument')

    response = requests.get("https://imdb-api.com/en/API/Search/" + os.getenv("IMDBAPI") + "/" + user_message)
    data = response.json()
    
    list = data['results']
    
    message = await ctx.message.channel.send('Search Query:')
    listcount = 0
    for thing in list:
        listcount += 1
        title = str(thing['title'])
        description = str(thing['description'])
        poster = thing['image']
        showurl = str("https://www.imdb.com/title/" + str(thing['id']))

        addButton = Button(label="Add", style=ButtonStyle.green,  custom_id='add')
        nextButton = Button(label="Next", style=ButtonStyle.red, custom_id='next')
        actionRow = ActionRow(addButton, nextButton)

        color = discord.Color.from_rgb(random.randint(0,255), random.randint(0,255), random.randint(0,255))

        embed=discord.Embed(
            title = title, 
            url = showurl, 
            description = description, 
            color = color).set_image(url = poster)
        embeded = await ctx.message.channel.send(embed=embed, components = [actionRow])

        interaction = await bot.wait_for(
            "button_click", check = lambda i: i.custom_id in ["add", "next"]
        )

        if interaction.custom_id == "add":
            try:
                search = sonarr.search_series(title)
                search[0].add("/tv", "HD-1080p", "English", search = True)
                await embeded.delete()
                await message.delete()
                await ctx.message.channel.send(embed=embed)
                await ctx.message.channel.send(title + ' had been added to Plex.')
            except arrapi.exceptions.Exists:
                await embeded.delete()
                await message.delete()
                await ctx.message.channel.send(embed=embed)
                await ctx.message.channel.send('That show already exists!')
            break
        else:
            await embeded.delete()
        
        if listcount == 5:
            await message.delete()
            await ctx.message.channel.send('`End of query`')
            break
    return



bot.run(TOKEN)
