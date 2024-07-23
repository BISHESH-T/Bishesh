from itertools import cycle
import asyncio
import discord
from discord.ext import commands, tasks
from discord import Embed, Colour
import json
from difflib import get_close_matches
from datetime import datetime
from bs4 import BeautifulSoup
import aiohttp
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
from dotenv import load_dotenv

client = commands.Bot(command_prefix='a!', intents=discord.Intents.all())
client.remove_command('help')


load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
         
class ChannelIdEventHandler(FileSystemEventHandler):
    def __init__(self, reload_callback):
        self.reload_callback = reload_callback

    def on_modified(self, event):
        if event.src_path.endswith('notification_channels.json'):
            print(f'File changed: {event.src_path}')
            self.reload_callback()

def reload_channel_ids():
    global Notifs_Channel
    channel_id = load_channel_id('notification_channels.json')
    Notifs_Channel = get_channel_ids(channel_id)
    print("Channel IDs reloaded!")   
            
# Functions to get current date and time
def current_date():
    now = datetime.now()
    return now.strftime("%Y-%m-%d")

def current_time():
    now = datetime.now()
    return now.strftime("%H:%M")


announced_campaigns = set()

# Load and save functions for the knowledge base
def load_knowledge_base(file_path: str) -> dict:
    with open(file_path, "r") as file:
        data: dict = json.load(file)
    return data

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)

knowledge_base = load_knowledge_base('knowledge_base.json')



# Function to find the best match for a question
def find_best_match(user_question: str, questions: list[str]) -> str | None:
    matches: list = get_close_matches(user_question, questions, n=1, cutoff=0.9)
    return matches[0] if matches else None

# Function to get the answer for a question
def get_answer_for_question(question: str, knowledge_base: dict) -> str | None:
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]

# Function to convert the quest start date from (July, 24, 2024) to (2024-07-24) format
def convert_date(date_str):
    date_parts = date_str.split(',')
    date_part = f"{date_parts[0].strip()} {date_parts[1].strip()}"
    input_format = "%b %d %Y"
    output_format = "%Y-%m-%d"
    date_obj = datetime.strptime(date_part, input_format)
    formatted_date = date_obj.strftime(output_format)
    return formatted_date


# Fetch function using aiohttp
async def fetch(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            return await response.text()
    except aiohttp.ClientError as e:
        print(f"Request error: {e}")
        return None

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    
    # Start file watcher for channel IDs
    observer = Observer()
    handler = ChannelIdEventHandler(reload_channel_ids)
    observer.schedule(handler, path='.', recursive=False)
    observer.start()
    
    # Start periodic tasks
    check_new_campaigns.start()
    bot_status_rotation.start()
    new_quest.start()
    
    


#A variable to set the noticiation time
notif_time = "08:45" #set the time in the form "H:M"

#A variable to store the timestamp value
unix_timestamp = int(time.time()) + 3600 # +3600 assuming that the quest is starting after an hour of the notification sent
timestamp_message = f"<t:{unix_timestamp}:R>"


#Load and save function for the channel id
def load_channel_id(file_path: str) -> dict:
    with open(file_path, "r") as file:
        data:dict = json.load(file)
    return data


def save_channel_id(file_path: str, data: dict):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)
        

        
def get_channel_ids(channel_id_data: dict) -> list:
    if "channel_ids" in channel_id_data:
        channel_ids = [channel["channel_id"] for channel in channel_id_data["channel_ids"]]
        return channel_ids
    return []


channel_id = load_channel_id('notification_channels.json')

Notifs_Channel = get_channel_ids(channel_id)


@client.command()
async def add_channel(ctx, id: int):
    channel_id["channel_ids"].append({"channel_id": id})
    save_channel_id("notification_channels.json", channel_id)
    await ctx.send("The channel has been added for notifications!")

                
    
    
    
#Task to check for new quests and notify the stackies
@tasks.loop(minutes=1)
async def new_quest():
    async with aiohttp.ClientSession() as session:
        try:
            html_text = await fetch(session, 'https://earn.stackup.dev/campaigns')
            if html_text is None:
                return  # Skip this iteration if there was an error

            soup = BeautifulSoup(html_text, 'lxml')
            campaigns = soup.find_all('li', class_='w-full sm:max-w-[276px] md:max-w-[296px] lg:max-w-[424px] xl:max-w-[368px] lg:w-1/2 xl:w-1/3 grayscale-11 rounded-3xl overflow-hidden border-l border-r border-b border-grayscale-8')
            
            for campaign in campaigns:
                try:
                    image = campaign.find('img', class_="object-fill aspect-[2/1]")['src']
                    name = campaign.find('h3').text
                    link = campaign.find('a')['href']
                    
                    html_quest = await fetch(session, f'https://earn.stackup.dev{link}')
                    if html_quest is None:
                        continue  # Skip this campaign if there was an error

                    soup2 = BeautifulSoup(html_quest, 'lxml')
                    quests = soup2.find_all('li', class_='group relative bg-white rounded-xl border border-grayscale-8')
                    
                    for quest in quests:
                        try:
                            quest_name = quest.find('h2').text
                            quest_status = quest.find('span').text
                            box_rewards = quest.find_all('div', class_="flex space-x-3 items-center")
                            quest_rewards = box_rewards[1].text
                            quest_link = quest.find('a', class_="p-5 flex flex-col space-y-5 md:p-8")['href']
                            
                            html_subquest = await fetch(session, f'https://earn.stackup.dev{quest_link}')
                            if html_subquest is None:
                                continue  # Skip this quest if there was an error

                            soup3 = BeautifulSoup(html_subquest, 'lxml')
                            box_date = soup3.find_all('time')
                            quest_start = [time.text for time in box_date]
                            quest_date = convert_date(quest_start[0])
                            present_date = current_date()
                            present_time = current_time()
                            if quest_date == present_date and present_time == notif_time:
                                for channel_id in Notifs_Channel:
                                    targeted_channel = client.get_channel(channel_id)
                                    await targeted_channel.send(f"Hey @stackies, \n{quest_name} of {name} campaign will start {timestamp_message}. Go check it out.\n\n Questions with answers found in the quest will be ignored. For those who like to help, please ask guiding questions instead of giving answers. This encourages learning and independence during the campaign.\n\n Ensure that you thoroughly review the screenshot you're submitting, verifying that it adheres to the correct formatting.")                        
                                    embed = discord.Embed(
                                        color=(discord.Colour.random()),
                                        description=f'''{quest_rewards}                
                                        **Status: ** {quest_status}
                                        ‎
                                        **Starts: ** {quest_start[0]}
                                        **Ends: ** {quest_start[1]}
                                        ‎
                                        [Quest Link](https://earn.stackup.dev{quest_link})''')
                                    embed.set_author(name=quest_name, url=f'https://earn.stackup.dev{quest_link}')
                                    embed.set_image(url=image)
                                    await targeted_channel.send(embed=embed)
                        except Exception as e:
                            print(f"Error processing quest: {e}")
                except Exception as e:
                    print(f"Error processing campaign: {e}")
        except Exception as e:
            print(f"Error fetching campaigns: {e}")
            
            
# Task to check for new campaigns
@tasks.loop(minutes=1)
async def check_new_campaigns():
    async with aiohttp.ClientSession() as session:
        html_text = await fetch(session, 'https://earn.stackup.dev/campaigns')
        if html_text is None:
            return

        soup = BeautifulSoup(html_text, 'lxml')
        campaigns = soup.find_all('li', class_='w-full sm:max-w-[276px] md:max-w-[296px] lg:max-w-[424px] xl:max-w-[368px] lg:w-1/2 xl:w-1/3 grayscale-11 rounded-3xl overflow-hidden border-l border-r border-b border-grayscale-8')

        for campaign in campaigns:
            image = campaign.find('img', class_="object-fill aspect-[2/1]")['src']
            name = campaign.find('h3').text
            link = campaign.find('a')['href']
            campaign_id = campaign.find('a')['href']
            box_date_div = campaign.find('div', class_="flex space-x-8 flex-row")
            box_date = box_date_div.find_all('span')
            campaign_start = box_date[0].text
            campaign_end = box_date[1].text
            status = campaign.find('span').text
            if status == "Upcoming" and campaign_id not in announced_campaigns:
                for channel_id in Notifs_Channel:
                    targeted_channel = client.get_channel(channel_id)
                    await targeted_channel.send("Hey @stackies, a new campaign is out. Go check it out.")
                    await targeted_channel.send("‎")
                    embed = discord.Embed(
                        color=discord.Colour.random(),
                        description=f'''
                            **Starts at:** {campaign_start}
                            **Ends at:** {campaign_end}
                            {'https://earn.stackup.dev' + link}''')
                    embed.set_author(name=name, url=f'https://earn.stackup.dev{link}')
                    embed.set_image(url=image)
                    await targeted_channel.send(embed=embed)
                    announced_campaigns.add(campaign_id)

#bot status
@tasks.loop(seconds=20)
async def bot_status_rotation():
    bot_statuses = ["a!help", "stackie.ie | a!help"]
    displaying = cycle(bot_statuses)
    while True:
        current_status = next(displaying)
        await client.change_presence(activity=discord.Game(current_status))
        await asyncio.sleep(20)


            
                    
                    
# Command to handle user queries and update knowledge base
@client.command(name='ask')
async def ask(ctx, *, user_input: str):
    best_match = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])
    if best_match:
        answer = get_answer_for_question(best_match, knowledge_base)
        await ctx.send(f'{answer}')
    else:
        await ctx.send("No solutions have been found yet. If you've solved it then please enlighten me. (You can also reply a!skip if you dont have the solution either.)   ```[NOTE: Do not enter anything weird as the bot learns from the user's response]```")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await client.wait_for('message', check=check, timeout=60.0)
            new_answer = msg.content

            if new_answer.lower() != "a!skip":
                knowledge_base["questions"].append({"question": user_input, "answer": new_answer})
                save_knowledge_base("knowledge_base.json", knowledge_base)
                await ctx.send("Thank you for the response!")
            else:
                await ctx.send("Okay, maybe next time!")
        except asyncio.TimeoutError:
            await ctx.send("Timed out. Please Try again.")


# Command to display ongoing campaigns
@client.command()
async def ongoing(ctx):
    await ctx.send("**THE CURRENTLY ONGOING CAMPAIGNS ARE:**")
    async with aiohttp.ClientSession() as session:
        html_text = await fetch(session, 'https://earn.stackup.dev/campaigns')
        if html_text is None:
            await ctx.send("Failed to retrieve campaigns.")
            return

        soup = BeautifulSoup(html_text, 'lxml')
        campaigns = soup.find_all('li', class_='w-full sm:max-w-[276px] md:max-w-[296px] lg:max-w-[424px] xl:max-w-[368px] lg:w-1/2 xl:w-1/3 grayscale-11 rounded-3xl overflow-hidden border-l border-r border-b border-grayscale-8')
        for campaign in campaigns:
            image = campaign.find('img', class_="object-fill aspect-[2/1]")['src']
            name = campaign.find('h3').text
            link = campaign.find('a')['href']
            box_date_div = campaign.find('div', class_="flex space-x-8 flex-row")
            box_date = box_date_div.find_all('span')
            campaign_start = box_date[0].text
            campaign_end = box_date[1].text
            status = campaign.find('span').text
            if status == "Ongoing":
                embed = discord.Embed(
                    color=discord.Colour.random(),
                    description=f'''
                        **Starts at:** {campaign_start}
                        **Ends at:** {campaign_end}
                        {'https://earn.stackup.dev' + link}
                    '''
                )
                embed.set_author(name=name, url=f'https://earn.stackup.dev{link}')
                embed.set_image(url=image)
                await ctx.send(embed=embed)
                await ctx.send("‎")

# Command to display upcoming campaigns
@client.command()
async def upcoming(ctx):
    await ctx.send("**THE UPCOMING CAMPAIGN IS:**")
    async with aiohttp.ClientSession() as session:
        html_text = await fetch(session, 'https://earn.stackup.dev/campaigns')
        if html_text is None:
            await ctx.send("Failed to retrieve campaigns.")
            return

        soup = BeautifulSoup(html_text, 'lxml')
        campaigns = soup.find_all('li', class_='w-full sm:max-w-[276px] md:max-w-[296px] lg:max-w-[424px] xl:max-w-[368px] lg:w-1/2 xl:w-1/3 grayscale-11 rounded-3xl overflow-hidden border-l border-r border-b border-grayscale-8')
        for campaign in campaigns:
            image = campaign.find('img', class_="object-fill aspect-[2/1]")['src']
            name = campaign.find('h3').text
            link = campaign.find('a')['href']
            box_date_div = campaign.find('div', class_="flex space-x-8 flex-row")
            box_date = box_date_div.find_all('span')
            campaign_start = box_date[0].text
            campaign_end = box_date[1].text
            status = campaign.find('span').text
            if status == "Upcoming":
                embed = discord.Embed(
                    color=discord.Colour.random(),
                    description=f'''
                        **Starts at:** {campaign_start}
                        **Ends at:** {campaign_end}
                        {'https://earn.stackup.dev' + link}
                    '''
                )
                embed.set_author(name=name, url=f'https://earn.stackup.dev{link}')
                embed.set_image(url=image)
                await ctx.send(embed=embed)
                await ctx.send("‎")
            elif status == "Ongoing":
                await ctx.send("**No Upcoming Campaigns**")
                await ctx.send("**THE LATEST CAMPAIGN IS: **")
                embed = discord.Embed(
                    color =(discord.Colour.random ()),
                    description = f'''
                                **Starts at:** {campaign_start}
                                **Ends at:** {campaign_end}
                                {'https://earn.stackup.dev' + link}
                                ''')
                embed.set_author(name=name, url = f'{'https://earn.stackup.dev' + link}')
                embed.set_image(url=image)
                await ctx.send(embed=embed)
                break
                
                
#command to find and update the quest info within campaigns
@client.command(name='quest')
async def quest(ctx):
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    async def fetch(session, url):
        try:
            async with session.get(url, timeout=10) as response:
                return await response.text()
        except aiohttp.ClientError as e:
            print(f"Request error: {e}")
            return None

    async def get_campaigns(session):
        html_text = await fetch(session, 'https://earn.stackup.dev/campaigns')
        if html_text is None:
            return []
        soup = BeautifulSoup(html_text, 'lxml')
        return soup.find_all('li', class_='w-full sm:max-w-[276px] md:max-w-[296px] lg:max-w-[424px] xl:max-w-[368px] lg:w-1/2 xl:w-1/3 grayscale-11 rounded-3xl overflow-hidden border-l border-r border-b border-grayscale-8')

    await ctx.send("**Which Campaign's Quests would you like to check?**")
    await ctx.send("‎")

    async with aiohttp.ClientSession() as session:
        campaigns = await get_campaigns(session)

        if not campaigns:
            await ctx.send("Failed to retrieve campaigns.")
            return

        ongoing_campaigns = []
        upcoming_campaigns = []
        
        for i, campaign in enumerate(campaigns, start=1):
            image = campaign.find('img', class_="object-fill aspect-[2/1]")['src']
            name = campaign.find('h3').text
            link = campaign.find('a')['href']
            box_date_div = campaign.find('div', class_="flex space-x-8 flex-row")
            box_date = box_date_div.find_all('span')
            campaign_start = box_date[0].text 
            campaign_end = box_date[1].text 
            status = campaign.find('span').text

            if status == "Ongoing":
                ongoing_campaigns.append((i, campaign))
                embed = discord.Embed(
                    color=discord.Colour.random(),
                    description=f'''
                        **Starts at:** {campaign_start}
                        **Ends at:** {campaign_end}
                        [Campaign Link](https://earn.stackup.dev{link})
                    ''')
                embed.set_author(name=f'{i}. {name}', url=f'https://earn.stackup.dev{link}')
                embed.set_image(url=image)
                await ctx.send(embed=embed)
            else:
                upcoming_campaigns.append((i, campaign))
        
        if not ongoing_campaigns:
            await ctx.send("No ongoing campaigns found.")
        else:
            await ctx.send("```Reply with the number of the Campaign:```")

            try:
                msg = await client.wait_for('message', check=check, timeout=60.0)
                index_campaign = int(msg.content)
                if not (1 <= index_campaign <= len(ongoing_campaigns)):
                    await ctx.send("Invalid number. Please try again.")
                    return
            except (ValueError, asyncio.TimeoutError):
                await ctx.send("Invalid input or timeout. Please try again.")
                return

            specific_campaign = ongoing_campaigns[index_campaign - 1][1]
            image = specific_campaign.find('img', class_="object-fill aspect-[2/1]")['src']
            name = specific_campaign.find('h3').text
            link = specific_campaign.find('a')['href']
            
            html_quest = await fetch(session, f'https://earn.stackup.dev{link}')
            if html_quest is None:
                await ctx.send("Unable to fetch campaign details. Please try again later.")
                return

            soup2 = BeautifulSoup(html_quest, 'lxml')
            quests = soup2.find_all('li', class_='group relative bg-white rounded-xl border border-grayscale-8')

            embed = discord.Embed(color=discord.Colour.random())
            embed.set_author(name=name, url=f'https://earn.stackup.dev{link}')
            embed.set_image(url=image)
            await ctx.send(embed=embed)

            for quest in quests:
                quest_name = quest.find('h2').text
                quest_status = quest.find('span').text
                box_rewards = quest.find_all('div', class_="flex space-x-3 items-center")
                quest_rewards = box_rewards[1].text
                quest_link = quest.find('a', class_="p-5 flex flex-col space-y-5 md:p-8")['href']
                
                html_subquest = await fetch(session, f'https://earn.stackup.dev{quest_link}')
                if html_subquest is None:
                    continue

                soup3 = BeautifulSoup(html_subquest, 'lxml')
                box_date = soup3.find_all('time')
                quest_date = [time.text for time in box_date]

                embed = discord.Embed(
                    color=discord.Colour.random(),
                    description=f'''{quest_rewards}
                        **Status: ** {quest_status}
                        ‎
                        **Starts: ** {quest_date[0]}
                        **Ends: ** {quest_date[1]}
                        ‎
                        https://earn.stackup.dev{quest_link}
                    '''
                )
                embed.set_author(name=quest_name, url=f'https://earn.stackup.dev{quest_link}')
                await ctx.send(embed=embed)


@client.command()
async def info(ctx):
    embed = discord.Embed(title = "Here's more info related to Stackie bot",
    description = "Hi there! I'm ``Stackie``:smile:, a multi-purpose bot crafted entirely in Python :snake:. I was brough in this digital realm in :two::zero::two::four: by the one and only ``Sakuta ``:sparkles:. Stackie is here to serve, assist, and entertain in the virtual worlds that he calls home:house_with_garden:. Try out ``a!ask <query>`` to get help regarding the current quest. Check ``a!help`` for more of my commands.  Happy hacking!! :blush:")

    await ctx.send(embed=embed)
    
    
@client.command()
async def help(ctx):
    embed = discord.Embed(title ="Stackie's commands", description= "Here are the commands for Stackie. My prefix is **a!**, ``a!<command>`` ",
    color= discord.Colour.random())
    embed.add_field(name=":blush:Checkout the Ongoing and Upcoming Campaigns", value ="``ongoing``, ``upcoming``", inline = False)
    embed.add_field(name=":smirk_cat: Check out the Quests within the Campaigns", value ="``quest``",inline=False)
    embed.add_field(name=":sunglasses: Get Quest Help from AI", value = "``ask <query>``",inline=False)
    embed.add_field(name=":heart_eyes:More About Stackie", value="``info``",inline=False)
    embed.add_field(name=":smile:More features of Stackie", value="Stackie has the feature of notifying the stackies with the new campaigns and quests on quest days Automatically. Make sure to set up a notification channel by using the command ``a!add_channel <channel_id>``.",inline=False)
    
    
    await ctx.send(embed=embed)








# Run the bot
client.run(BOT_TOKEN)
