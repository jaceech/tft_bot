import discord
from discord.ext import commands
from riotwatcher import TftWatcher
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import io

load_dotenv()

intents = discord.Intents.all()
intents.messages = True

discord_bot_key = os.getenv('DISCORD_KEY')
riot_api_key = os.getenv('RIOT_KEY')

bot = commands.Bot(command_prefix='?', intents=intents)
tft_watcher = TftWatcher(riot_api_key)

@bot.event
async def on_ready():
    print(f'{bot.user.name} is online')

@bot.command(name='search', help='Gets TFT rank and match history for a summoner')
async def search_tft(ctx, username):
    try:
        # Get summoner information
        summoner = tft_watcher.summoner.by_name('na1', username)
        puuid = summoner.get('puuid')

        if not puuid:
            await ctx.send(f'Error: Unable to find PUUID for {username}')
            return

        # Get TFT rank information
        tft_stats = tft_watcher.league.by_summoner('na1', summoner['id'])

        if not tft_stats:
            await ctx.send(f'No TFT data found for {username}')
            return

        tft_info = tft_stats[0]
        tier = tft_info['tier']
        rank = tft_info['rank']
        lp = tft_info['leaguePoints']
        wins = tft_info['wins']
        losses = tft_info['losses']

        response = (
            f'{username} is {tier} {rank} - {lp} LP\n'
            f'{wins}W - {losses}L'
        )

        # Get TFT match history
        match_ids = tft_watcher.match.by_puuid('na1', puuid, 30)  

        # Extract placements from the last matches
        placements = []
        for match_id in match_ids:
            match_data = tft_watcher.match.by_id('na1', match_id)
            for participant in match_data['info']['participants']:
                if participant['puuid'] == puuid:
                    placements.append(participant['placement'])

        # Count the occurrences of each placement
        placement_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0}
        for placement in placements:
            placement_counts[placement] += 1

        # Create a bar graph
        plt.figure(figsize=(8, 6))
        plt.bar(placement_counts.keys(), placement_counts.values())
        plt.title('TFT Placements in your Last 30 Matches')
        plt.xlabel('Placement')
        plt.ylabel('Number of Games')

        # Save the plot to a BytesIO object
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)

        # Send the response and the bar graph as an image
        await ctx.send(response, file=discord.File(img_buf, 'placements.png'))

    except Exception as e:
        await ctx.send(f'Error: {e}')

bot.run(discord_bot_key)

