import requests
import discord
from discord.ext import commands
from discord import ui, SelectOption,InteractionType
from collections import defaultdict
import asyncio
import datetime
import re

TOKEN = 'MTA5Njc4Mjg1OTgyNzY4MzQ1OA.GfkTFy.9ZOQ1bnY93_m5zi5GDr-d6pyW1oSSEh0tilvrA' #redmonke6
API_KEY = 'nijPCMuokuDnPnf3'
ROLE_ID = ''
MAIN_TRACKER_ID = ''
FLIGHT_TRACKER_ID = ''
FACTION_ID = 19060
FACTION_ID2 = 26885
FACTION_ID3 = 8509
flight_tracker_message = None

intents = discord.Intents.all()
intents.members = True
client = commands.Bot(command_prefix="!", intents = discord.Intents.all())

url = f'https://www.tornstats.com/api/v2/{API_KEY}/spy/faction/{FACTION_ID}'
response = requests.get(url)
data = response.json()

#Get faction stuff
faction_name = data["faction"]['name']
faction_tag = data["faction"]['tag_image']

#Get ranked war data
current_ranked_wars = data["faction"]["ranked_wars"]
if current_ranked_wars:
    for key, value in current_ranked_wars.items():
        factions_dict = value.get('factions')
        if factions_dict:
            for sub_key, faction in factions_dict.items():
                if sub_key != str(FACTION_ID):
                    FACTION_OPPONENT = sub_key
                    FACTION_OPPONENT_NAME = faction.get('name')
                    #chain_count = faction.get('chain', 0)
                    print(f"FACTION_OPPONENT: {FACTION_OPPONENT}")
                    print(f"FACTION_OPPONENT_NAME: {FACTION_OPPONENT_NAME}")
                    #print(f"chain_count: {chain_count}")
        else:
            print("No factions data available")
else:
    print("No ranked wars available")

async def send_initial_message():
    while True:
        if MAIN_TRACKER_ID:
            break
        await asyncio.sleep(10)  # Check every 10 seconds
    
    await update_embedded_message()

@client.event
async def on_ready():
    print("Bot is ready")
    try:
        synced = await client.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
    #await send_initial_message()

    # Call the function to send the initial message
    await send_initial_message()
    if not MAIN_TRACKER_ID:
        # Get the guild (server) where the bot is connected
        guild = client.guilds[0]
        # Send an error message to the first text channel in the server
        for channel in guild.channels:
            if isinstance(channel, discord.TextChannel):
                embed = discord.Embed(title="Error", description="Please set the Status tracker channel first.", color=discord.Color.red())
                await channel.send(embed=embed)
                break

    client.loop.create_task(update_embedded_message())

class configdropdown(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options=[
            discord.SelectOption(label="Api Key", description="Set the main api key"),
            discord.SelectOption(label="Chain bonus watcher role", description="Set the chain bonus watcher role"),
            discord.SelectOption(label="Member Status Tracker", description="Set the main tracker channel"),
            discord.SelectOption(label="Flight Tracker", description="Set the flight tracker channel"),
            discord.SelectOption(label="Item Usage Tracker", description="Set the item usage tracker channel"),
        ]
        super().__init__(placeholder="Select an option", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected_option = self.values[0]
        if selected_option == "Api Key":
            # Prompt the user to input a new API key
            await interaction.response.send_message("Please enter a new API key:", ephemeral=True,delete_after=30)
            # Wait for the user's response
            response = await self.bot.wait_for("message", check=lambda m: m.author == interaction.user)
            # Update the API key with the user's input
            global API_KEY
            API_KEY = response.content
            # Delete the user's message
            await response.delete()
            # Mask the API key
            if API_KEY:
                masked_api_key = API_KEY[:-11] + "***********"
            else:
                masked_api_key = "Not set"
            # Edit the original message with the updated embedded message
            embed = discord.Embed(title=f"{faction_name} Ranked War bot", color=0x00ff00)
            embed.set_thumbnail(url=f"https://factiontags.torn.com/{faction_tag}")
            embed.set_footer(text="Ranked War bot provided by Monke Squad", icon_url="https://cdn.discordapp.com/avatars/1081162054968291359/8eafa7fefb85aa35be28ca8cea1e8be5.webp?size=128")
            embed.add_field(name="API Key", value=masked_api_key, inline=False)
            embed.add_field(name="Chain bonus watcher role", value=f"<@&{ROLE_ID}>" if ROLE_ID else "Not set", inline=False)
            if MAIN_TRACKER_ID:
                embed.add_field(name="Member Status Tracker", value=f"<#{MAIN_TRACKER_ID}>", inline=True)
            else:
                embed.add_field(name="Member Status Tracker", value="Not set", inline=True)
            if FLIGHT_TRACKER_ID:
                embed.add_field(name="Flight Tracker", value=f"<#{FLIGHT_TRACKER_ID}>", inline=True)
            else:
                embed.add_field(name="Flight Tracker", value="Not set", inline=True)

            view = discord.ui.View()
            view.add_item(configdropdown(self.bot))
            await interaction.message.edit(content="Configuration updated.", embed=embed, view=dropdownIn(self.bot))

        elif selected_option == "Chain bonus watcher role":
            # Prompt the user to select a role
            view = discord.ui.View()
            view.add_item(RoleDropdown(client, interaction))
            await interaction.response.send_message("Please select a chain bonus watcher role:", view=view, ephemeral=True,delete_after=30)
        elif selected_option == "Member Status Tracker":
            view = discord.ui.View()
            view.add_item(ChannelDropdown(client, interaction))
            await interaction.response.send_message("Please select a text channel for member status tracker:", view=view, ephemeral=True,delete_after=30)
        elif selected_option == "Flight Tracker":
            view = discord.ui.View()
            view.add_item(FlightDropdown(client, interaction))
            await interaction.response.send_message("Please select a text channel for flight tracker:", view=view, ephemeral=True,delete_after=30)

class ChannelDropdown(discord.ui.Select):
    def __init__(self, client, interaction):
        self.client = client
        self.interaction = interaction
        options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in client.guilds[0].text_channels]
        super().__init__(placeholder="Select a channel", options=options)

    async def callback(self, interaction: discord.Interaction):
        global MAIN_TRACKER_ID
        MAIN_TRACKER_ID = int(self.values[0])
        masked_api_key = API_KEY[:-11] + "***********" if API_KEY else "Not set"
        embed = discord.Embed(title=f"{faction_name} Ranked War bot", color=0x00ff00)
        embed.set_thumbnail(url=f"https://factiontags.torn.com/{faction_tag}")
        embed.set_footer(text="Ranked War bot provided by Monke Squad", icon_url="https://cdn.discordapp.com/avatars/1081162054968291359/8eafa7fefb85aa35be28ca8cea1e8be5.webp?size=128")
        embed.add_field(name="API Key", value=masked_api_key, inline=False)
        embed.add_field(name="Chain bonus watcher role", value=f"<@&{ROLE_ID}>" if ROLE_ID else "Not set", inline=False)
        if MAIN_TRACKER_ID:
            embed.add_field(name="Member Status Tracker", value=f"<#{MAIN_TRACKER_ID}>", inline=True)
        else:
            embed.add_field(name="Member Status Tracker", value="Not set", inline=True)
        if FLIGHT_TRACKER_ID:
            embed.add_field(name="Flight Tracker", value=f"<#{FLIGHT_TRACKER_ID}>", inline=True)
        else:
            embed.add_field(name="Flight Tracker", value="Not set")
        await interaction.response.send_message(content=f"Member status tracker channel has been set to <#{MAIN_TRACKER_ID}>.", embed=embed, view=dropdownIn(self.client))

class FlightDropdown(discord.ui.Select):
    def __init__(self, client, interaction):
        self.client = client
        self.interaction = interaction
        options = [discord.SelectOption(label=channel.name, value=str(channel.id)) for channel in client.guilds[0].text_channels]
        super().__init__(placeholder="Select a channel", options=options)

    async def callback(self, interaction: discord.Interaction):
        global FLIGHT_TRACKER_ID
        FLIGHT_TRACKER_ID = int(self.values[0])
        masked_api_key = API_KEY[:-11] + "***********" if API_KEY else "Not set"
        embed = discord.Embed(title=f"{faction_name} Ranked War bot", color=0x00ff00)
        embed.set_thumbnail(url=f"https://factiontags.torn.com/{faction_tag}")
        embed.set_footer(text="Ranked War bot provided by Monke Squad", icon_url="https://cdn.discordapp.com/avatars/1081162054968291359/8eafa7fefb85aa35be28ca8cea1e8be5.webp?size=128")
        embed.add_field(name="API Key", value=masked_api_key, inline=False)
        embed.add_field(name="Chain bonus watcher role", value=f"<@&{ROLE_ID}>" if ROLE_ID else "Not set", inline=False)
        if MAIN_TRACKER_ID:
            embed.add_field(name="Member Status Tracker", value=f"<#{MAIN_TRACKER_ID}>", inline=True)
        else:
            embed.add_field(name="Member Status Tracker", value="Not set", inline=True)
        if FLIGHT_TRACKER_ID:
            embed.add_field(name="Flight Tracker", value=f"<#{FLIGHT_TRACKER_ID}>", inline=True)
        else:
            embed.add_field(name="Flight Tracker", value="Not set", inline=True)
        await interaction.response.send_message(content=f"Flight tracker channel has been set to <#{FLIGHT_TRACKER_ID}>.", embed=embed, view=dropdownIn(self.client))


class RoleDropdown(discord.ui.Select):
    def __init__(self, client, interaction):
        self.client = client
        self.interaction = interaction
        options = [discord.SelectOption(label=role.name, value=str(role.id)) for role in client.guilds[0].roles]
        super().__init__(placeholder="Select a role", options=options)

    async def callback(self, interaction: discord.Interaction):
        # Update the ROLE_ID variable with the selected role
        global ROLE_ID
        ROLE_ID = int(self.values[0])
        # Edit the original message with the updated embedded message
        masked_api_key = API_KEY[:-11] + "***********" if API_KEY else "Not set"
        embed = discord.Embed(title=f"{faction_name} Ranked War bot", color=0x00ff00)
        embed.set_thumbnail(url=f"https://factiontags.torn.com/{faction_tag}")
        embed.set_footer(text="Ranked War bot provided by Monke Squad", icon_url="https://cdn.discordapp.com/avatars/1081162054968291359/8eafa7fefb85aa35be28ca8cea1e8be5.webp?size=128")
        embed.add_field(name="API Key", value=masked_api_key, inline=False)
        embed.add_field(name="Chain bonus watcher role", value=f"<@&{ROLE_ID}>" if ROLE_ID else "Not set", inline=False)
        if MAIN_TRACKER_ID:
            embed.add_field(name="Member Status Tracker", value=f"<#{MAIN_TRACKER_ID}>", inline=True)
        else:
            embed.add_field(name="Member Status Tracker", value="Not set", inline=True)
        if FLIGHT_TRACKER_ID:
            embed.add_field(name="Flight Tracker", value=f"<#{FLIGHT_TRACKER_ID}>", inline=True)
        else:
            embed.add_field(name="Flight Tracker", value="Not set", inline=True)
        await interaction.response.send_message(content=f"Chain bonus watcher role has been set to <@&{ROLE_ID}>.", embed=embed, view=dropdownIn(self.client))
        # Get the role object for the current ROLE_ID
        role = interaction.guild.get_role(ROLE_ID)

class configbutton(discord.ui.Button):
    def __init__(self, bot):
        super().__init__(style=discord.ButtonStyle.primary, label="Click here to configure", row=0)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # Get the role object for the current ROLE_ID
        role = interaction.guild.get_role(ROLE_ID)
        # Create a response message with the current config
        masked_api_key = API_KEY[:-11] + "***********" if API_KEY else "Not set"
        role_mention = f"<@&{role.id}>" if role else "Not set"
        embed = discord.Embed(title="Current Config", color=0x00ff00)
        embed.add_field(name="API Key", value=masked_api_key)
        embed.add_field(name="Chain bonus watcher role", value=role_mention)
        embed.set_view(dropdownIn(client))
        await interaction.response.send_message(embed=embed, ephemeral=True)
        # Send the response message as an ephemeral message to the user
        #await interaction.response.send_message(embed=embed, ephemeral=True)
        # Create a new view with the dropdown menu
        view = discord.ui.View()
        view.add_item(configdropdown(self.bot))
        # Send a message with the view and the button
        message = await interaction.followup.send("Select an option to configure:", view=view)
        view.message = message



class dropdownIn(discord.ui.View):
    def __init__(self, bot):
        super().__init__()
        self.add_item(configdropdown(bot))


@client.tree.command(name="config", description="Ranked war bot configuration")
async def config(interaction: discord.Interaction):
    # Mask the API key
    if API_KEY:
        masked_api_key = API_KEY[:-11] + "***********"
    else:
        masked_api_key = "Not set"
    # Get the role object for the current ROLE_ID
    role = interaction.guild.get_role(ROLE_ID)
    # Get the channel object for the current MAIN_TRACKER_ID
    channel = interaction.guild.get_channel(MAIN_TRACKER_ID)
    flight_channel = interaction.guild.get_channel(FLIGHT_TRACKER_ID)
    # Create the embedded message
    embed = discord.Embed(title=f"{faction_name} Ranked War bot", color=0x00ff00)
    embed.set_thumbnail(url=f"https://factiontags.torn.com/{faction_tag}")
    embed.set_footer(text="Ranked War bot provided by Monke Squad", icon_url="https://cdn.discordapp.com/avatars/1081162054968291359/8eafa7fefb85aa35be28ca8cea1e8be5.webp?size=128")
    embed.add_field(name="API Key", value=masked_api_key, inline=False)
    # Add the role field to the embedded message
    if role:
        embed.add_field(name="Chain bonus watcher role", value=f"<@&{role.id}>", inline=False)
    else:
        embed.add_field(name="Chain bonus watcher role", value="Not set", inline=False)
    # Add the main tracker channel field to the embedded message
    if channel:
        embed.add_field(name="Member Status Tracker", value=f"<#{channel.id}>", inline=True)
    else:
        embed.add_field(name="Member Status Tracker", value="Not set", inline=True)
    if flight_channel:
        embed.add_field(name="Member Status Tracker", value=f"<#{flight_channel.id}>", inline=True)
    else:
        embed.add_field(name="Member Status Tracker", value="Not set", inline=True)
    
    # Send the embedded message with the dropdown view
    await interaction.response.send_message(embed=embed, view=dropdownIn(client), ephemeral=False)


message_objects = []  # Add this line before calling update_embedded_message function
async def update_embedded_message():
    global flight_tracker_message
    global FACTION_OPPONENT
    global ROLE_ID
    global FACTION_OPPONENT_NAME
    role_mention = f"<@&{ROLE_ID}>"
    sent_ping = False
    member_eta = {}
    while True:
        url2 = f'https://www.tornstats.com/api/v2/{API_KEY}/spy/faction/{FACTION_OPPONENT}'
        response2 = requests.get(url2)
        data2 = response2.json()

        def format_number(number):
            if number >= 10**9:
                return f"{number/10**9:.1f}B"
            elif number >= 10**6:
                return f"{number/10**6:.1f}M"
            elif number >= 10**3:
                return f"{number/10**3:.1f}K"
            else:
                return str(number)
        flight_durations = { #in minutes
            'Mexico': 18,
            'Cayman Islands': 25,
            'Canada': 29,
            'Hawaii': 94,
            'United Kingdom': 111,
            'Argentina': 117,
            'Switzerland': 123,
            'Japan': 158,
            'China': 169,
            'UAE': 190,
            'South Africa': 208,
            'Torn' : 0
        }
        country_flags = {        
            'Mexico': ":flag_mx: ",
            'Cayman Islands': ":flag_ky: ",
            'Canada': ":flag_ca:",
            'Hawaii': ":coconut:",
            'United Kingdom': ":england:",
            'Argentina': ":flag_ar:",
            'Switzerland': ":flag_ch:",
            'Japan': ":flag_jp:",
            'China': ":flag_cn:",
            'UAE': ":flag_ae:",
            'South Africa': ":flag_za:",
            'Torn' : ":pirate_flag: "
            # Add more countries and their flags here if needed
        }

        # Define the chain numbers to ping the role
        chain_numbers = [90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 460, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 990, 991, 992, 993, 994, 995, 996, 997, 998, 999, 2490]

        def format_countdown(hospital_timer):
            # Convert UNIX timestamp to datetime object
            dt_object = datetime.datetime.fromtimestamp(hospital_timer)
            # Calculate time difference
            time_difference = dt_object - datetime.datetime.now()
            # Format time difference as string
            hours, remainder = divmod(time_difference.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            countdown = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            return countdown
            
        def format_eta(eta_unix_timestamp, current_time):
            eta_datetime = datetime.datetime.fromtimestamp(eta_unix_timestamp)
            time_remaining = eta_datetime - current_time
            if time_remaining.total_seconds() < 0:
                return ""
            else:
                hours, remainder = divmod(time_remaining.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            
        faction_opp_name = data2["faction"]['name']
        faction_opp_tag = data2["faction"]['tag_image']

        class CountrySelect(ui.Select):
            def __init__(self, country_dict, member_eta ):
                options = [
                    discord.SelectOption(label=country, value=country)
                    for country in country_dict.keys()
                ]
                super().__init__(placeholder="Select a country", options=options)
                self.country_dict = country_dict
                self.member_eta = member_eta

            async def callback(self, interaction: discord.Interaction):
                selected_country = self.values[0]
                members_list = self.country_dict[selected_country]["members"]
                current_time = datetime.datetime.now()  # Get the current datetime object
                members_text = []
                for member in members_list:
                    member_id = member[2]

                    eta_info = self.member_eta.get(member_id, {})
                    eta_unix_timestamp = eta_info.get('eta')

                    if eta_unix_timestamp is not None:
                        remaining_time = format_eta(eta_unix_timestamp, current_time)
                        members_text.append(
                            f"{'✈️' if member[4] == 'Traveling' else '🏝️' if member[4] == 'Returning' else '🏝️'} **{member[0]}** [Profile](https://www.torn.com/profiles.php?XID={member_id}) - BS: {format_number(member[3])} - ETA: <t:{eta_unix_timestamp}:R> ({remaining_time})"
                        )
                    else:
                        members_text.append(
                            f"{'✅' if member[4] == 'Here' else '🏝️' if member[4] == 'Flying' else '🏝️'} **{member[0]}** [Profile](https://www.torn.com/profiles.php?XID={member_id}) - BS: {format_number(member[3])}"
                        )

                members_text = "\n".join(members_text)
                response_embed = discord.Embed(
                    title=f"{FACTION_OPPONENT_NAME} Members in {selected_country}",
                    color=discord.Color.blue(),
                    description=members_text
                )
                footer_text = "✈️ : Traveling   🏝️ : Abroad"
                response_embed.set_footer(text=footer_text)

                await interaction.response.send_message(embed=response_embed, ephemeral=True)



        okay_members = data2.get('faction', {}).get('members')
        online_members = []
        for member_id, member_info in okay_members.items():
            if member_info['last_action']['status'] == 'Online' and member_info['status']['state'] == 'Okay':
                spy_data = member_info.get('spy', {})
                total_spies = spy_data.get('total', 0)
                online_members.append([member_info['name'], member_info['level'], member_id, total_spies])
        
        # Extract hospitalized member data from the Torn API response
        hospitalize_members = data2.get('faction', {}).get('members')
        hospital_members = []
        for member_id, member_info in hospitalize_members.items():
            if member_info['status']['state'] == 'Hospital':
                # Extract member spy data
                spy_data = member_info.get('spy', {})
                total_spies = spy_data.get('total', 0)
                # Extract member status description
                status_description = member_info['status']['description']
                # Extract member hospital timer
                hospital_timer = member_info['status']['until']
                # Convert UNIX timestamp to datetime object
                dt_object = datetime.datetime.fromtimestamp(hospital_timer)
                # Convert datetime object to epoch time
                #epoch_time = int(dt_object.strftime('%s'))
                # Append member data to online_members list
                hospital_members.append([
                    member_info['name'], member_info['level'], member_id,
                    total_spies, status_description, hospital_timer
                ])
                # Add countdown for member hospital timer
                countdown = format_countdown(hospital_timer)
                hospital_members[-1].append(countdown)

        for key in data2["faction"]["ranked_wars"]:
        # Access the "factions" dictionary for each key
            current_chain = data2["faction"]["ranked_wars"][key]["factions"][str(
            FACTION_OPPONENT)]["chain"]
            #print(current_chain)

        current_time2 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Move this line inside the loop
        embed_chain = discord.Embed(title=f":chains: {faction_opp_name} Current Chain", color=discord.Color.gold())
        embed_chain.add_field(name="", value=f"**{current_chain}**")
        embed_chain.set_thumbnail(url=f"https://factiontags.torn.com/{faction_opp_tag}")
        embed_chain.set_footer(text=f"Updated at {current_time2}")

        online_members.sort(key=lambda x: x[0])
        hospital_members.sort(key=lambda x: x[-1])

        online_members_list = [
            f"**{member[0]}**, {member[1]}, [Profile](https://www.torn.com/profiles.php?XID={member[2]}) - BS: {format_number(member[3])},[Attack](https://www.torn.com/loader.php?sid=attack&user2ID={member[2]})"
            for member in online_members
        ]
        hospital_members_list = [
        f"**{member[0]}**, {member[1]}, [Profile](https://www.torn.com/profiles.php?XID={member[2]}) - BS: {format_number(member[3])} - Time Left: {member[6]}"
        for member in hospital_members
        ]

        if not online_members_list:
            message = "No online and okay member at this time"
        else:
            message = "\n".join(online_members_list)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Move this line inside the loop
        embed_online = discord.Embed(title=f":green_circle: Okay {faction_opp_name} Members", color=discord.Color.green(), description=message)
        embed_online.set_thumbnail(url=f"https://factiontags.torn.com/{faction_opp_tag}")
        embed_online.set_footer(text=f"Updated at {current_time}")

        if not hospital_members_list:
            message = "No hospitalize member at this time"
        else:
            message = "\n".join(hospital_members_list)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Move this line inside the loop
        embed_hospital = discord.Embed(title=f":red_circle: Hospitalize {faction_opp_name} Members", color=discord.Color.red(), description=message)
        embed_hospital.set_thumbnail(url=f"https://factiontags.torn.com/{faction_opp_tag}")
        embed_hospital.set_footer(text=f"Updated at {current_time}")

        # Extract travel member data from the Torn API response
        traveling_members = data2.get('faction', {}).get('members')
        travel_members = []
        country_dict = defaultdict(lambda: {"flying": 0, "here": 0, "returning": 0, "members": []})
        country_dict["Torn"] = {"flying": 0, "here": 0, "returning": 0, "members": []}
        for member_id, member_info in traveling_members.items():
            if 'Traveling' in member_info['status']['state'] or 'Returning to Torn from' in member_info['status']['description'] or 'Abroad' in member_info['status']['state']:
              
                # Extract member spy data
                spy_data = member_info.get('spy', {})
                total_spies = spy_data.get('total', 0)
                
                # Extract member status description
                status_description = member_info['status']['description']
                
                # Check if the member is returning to Torn
                if "Returning to Torn from" in status_description:
                    destination = "Torn"
                else:
                    # Extract the member's destination from their status description
                    destination_match = re.search(r"(?:Traveling to|Returning to Torn from|In) (.+)$", status_description)
                    if destination_match:
                        destination = destination_match.group(1)
                    else:
                        destination = None
                
                if destination:
                    if member_info['status']['state'] == 'Traveling':
                        country_dict[destination]["flying"] += 1
                    elif "Returning" in member_info['status']['description']:
                        country_dict["Torn"]["returning"] += 1
                    else:  # member_info['status']['state'] == 'Abroad'
                        country_dict[destination]["here"] += 1

                    eta_unix_timestamp = None    
                    if member_info['status']['state'] == 'Traveling' or 'Returning to Torn from' in member_info['status']['description']:
                        # Get the current time
                        current_time = datetime.datetime.now()

                        # Calculate the ETA based on the flight duration
                        destination_match = re.search(r"(?:Traveling to|Returning to Torn from) (.+)$", member_info['status']['description'])
                        if destination_match:
                            destination = destination_match.group(1)
                            flight_duration = flight_durations.get(destination, 0) * 60
                            eta = current_time.timestamp() + flight_duration
                            eta_unix_timestamp = int(eta)  # Convert to Unix timestamp

                            # Convert Unix timestamp to a datetime object
                            eta_datetime = datetime.datetime.fromtimestamp(eta_unix_timestamp)

                            # Calculate the time remaining
                            time_remaining = eta_datetime - current_time

                    # Append member data to travel_members list
                    if "Returning" in member_info['status']['description']:
                        country_dict["Torn"]["members"].append(
                            (member_info['name'], member_info['level'], member_id, total_spies, member_info['status']['state'], eta_unix_timestamp, destination)
                        )
                    else:
                        country_dict[destination]["members"].append(
                            (member_info['name'], member_info['level'], member_id, total_spies, member_info['status']['state'], eta_unix_timestamp, destination)
                        )


        for member in travel_members:
            if len(member) > 4:
                destination_match = re.search(r"(?:Traveling to|Returning to Torn from) (.+)$", status_description)
            else:
                destination_match = None
                if destination_match:
                    destination = destination_match.group(1)
                    if destination not in country_dict:
                        country_dict[destination] = {"flying_count": 0, "present_count": 0, "returning_count": 0, "members": []}

                    if "Returning" in member[4]:
                        country_dict[destination]["returning_count"] += 1
                    elif "Traveling" in member[4]:
                        country_dict[destination]["flying_count"] += 1
                    else:
                        country_dict[destination]["present_count"] += 1
                    country_dict[destination]["members"].append(member)

        # Add this block of code to update member_eta
        current_time = datetime.datetime.now()
        for country, country_data in country_dict.items():
            for member in country_data['members']:
                member_id = member[2]
                eta_info = member_eta.get(member_id, {})
                eta_unix_timestamp = eta_info.get('eta')
                timestamp = eta_info.get('timestamp')
                if eta_unix_timestamp is None or timestamp is None:
                    if member[4] == 'Traveling' or 'Returning to Torn from' in member[4]:
                        destination = member[6]
                        flight_duration = flight_durations.get(destination, 0) * 60
                        eta = current_time.timestamp() + flight_duration
                        eta_unix_timestamp = int(eta)
                        timestamp = current_time

                    else:
                        eta_unix_timestamp = None
                        timestamp = None

                    member_eta[member_id] = {'eta': eta_unix_timestamp, 'timestamp': timestamp}

        # Update the embed_travel here
        embed_travel = discord.Embed(title="Flight Tracker", color=discord.Color.blue())
        for country, data in country_dict.items():
            flag = country_flags.get(country, "")  # Get the flag emoji, or an empty string if not found
            if country == "Torn":
                embed_travel.add_field(
                    name=f"{flag} {country}",
                    value=f"   {data['flying']} people flying here",
                    inline=False
                )
            else:
                embed_travel.add_field(
                    name=f"{flag} {country}",
                    value=f"   {data['flying']} people flying here\n    {data['here']} people {'is' if data['here'] == 1 else 'are'} here",
                    inline=False
                )

        country_options = [
            SelectOption(label=country, value=country) for country in country_dict.keys()
        ]

        select_menu = discord.ui.Select(placeholder="Select a country", options=country_options)

        def format_eta2(eta_unix_timestamp, current_time):
            eta_datetime = datetime.datetime.fromtimestamp(eta_unix_timestamp)
            time_remaining = eta_datetime - current_time
            if time_remaining.total_seconds() < 0:
                return ""
            else:
                return int(eta_unix_timestamp)


        xanax_tracker = data2.get('faction', {}).get('members')
        xanax_cd = 480  # in minutes
        xanax_data = []
        for member_id, member_info in xanax_tracker.items():
            xanax_taken = member_info.get('personalstats', {}).get('Xanax Taken')
            timestamp = member_info.get('personalstats', {}).get('timestamp')
            xanax_name = member_info.get('name')
            xanax_level = member_info.get('level')
            xanax_id = member_info.get('id')

            if timestamp:
                eta_unix_timestamp = timestamp + xanax_cd * 60
                current_time = int(datetime.datetime.now().timestamp())
                time_remaining = eta_unix_timestamp - current_time
                if 0 <= time_remaining <= xanax_cd * 60:
                    # Include member data in the list
                    member_data = (xanax_name, xanax_level, eta_unix_timestamp, xanax_id)
                    xanax_data.append(member_data)

        xanax_data.sort(key=lambda x: x[0])

        xanax_members_list = [
            f"**{member[0]}**, {member[1]}, [Profile](https://www.torn.com/profiles.php?XID={member[3]}) - ETA: <t:{member[2]}:R>"
            for member in xanax_data
        ]

        if not xanax_members_list:
            message = "No Xanax member data available at this time."
        else:
            message = "\n".join(xanax_members_list)

        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
        embed_xanax = discord.Embed(
            title="Xanax Cooldown Tracker",
            color=discord.Color.red(),
            description=message
        )
        embed_xanax.set_footer(text=f"Updated at {formatted_time}")
        embed_xanax.set_thumbnail(url=f"https://www.torn.com/images/items/206/large.png")

        # Send or edit the embedded message based on the MAIN_TRACKER_ID
        if MAIN_TRACKER_ID:
            channel = await client.fetch_channel(MAIN_TRACKER_ID)
            if len(message_objects) == 4:
                # Edit the existing messages
                await message_objects[0].edit(embed=embed_online)
                await message_objects[1].edit(embed=embed_hospital)
                await message_objects[2].edit(embed=embed_chain)
                await message_objects[3].edit(embed=embed_xanax)
            else:
                # Send the messages for the first time
                msg_online = await channel.send(embed=embed_online)
                msg_hospital = await channel.send(embed=embed_hospital)
                msg_chain = await channel.send(embed=embed_chain)
                msg_xanax = await channel.send(embed=embed_xanax)
                message_objects.extend([msg_online, msg_hospital, msg_chain, msg_xanax])
        else:
            break

        if current_chain in chain_numbers and not sent_ping:
            await channel.send(f"{role_mention} {faction_opp_name}'s Chain is at {current_chain}!")
            sent_ping = True
        elif current_chain not in chain_numbers:
            sent_ping = False

        if FLIGHT_TRACKER_ID:
            travel_channel = await client.fetch_channel(FLIGHT_TRACKER_ID)
            select_menu = CountrySelect(country_dict, member_eta)

            # Create a ui.View and add the select_menu to it
            view = discord.ui.View()
            view.add_item(select_menu)

            # Check if the flight_tracker_message exists and edit it, otherwise send a new message
            if flight_tracker_message:
                await flight_tracker_message.edit(embed=embed_travel, view=view)
            else:
                flight_tracker_message = await travel_channel.send(embed=embed_travel, view=view)

        # Make a request to the Discord API
        response4 = requests.get('https://discord.com/api/v9/users/@me', headers={'Authorization': 'Bot MTA4ODUwOTIxMzAzMjA1ODk4Mg.GbfUU5.Ji5dzX-_KN95HKcUy_RTcgzm5OGv2p_NEpYO7s'})

        # Get the rate limit headers from the response
        limit = response4.headers.get('X-RateLimit-Limit')
        remaining = response4.headers.get('X-RateLimit-Remaining')
        reset_timestamp = response4.headers.get('X-RateLimit-Reset')

        print(f"Rate limit: {limit}, Remaining: {remaining}, Reset timestamp: {reset_timestamp}")

        await asyncio.sleep(60)

client.run(TOKEN)
