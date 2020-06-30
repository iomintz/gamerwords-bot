# Copyright 2020 io mintz <io@mintz.cc>
# Copyright 2020 Vex

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software
# is furnished to do so, subject to the following conditions:

# The above copyright notice, penisbird and this permission notice shall be included
# in all copies or substantial portions of the Software unmodified.

#                     _..._
#                  .-'     '-.
#                 /     _    _\
#                /':.  (o)  /__)
#               /':. .,_    |  |
#              |': ; /  \   /_/
#              /  ;  `"`"    }
#             ; ':.,         {
#            /      ;        }
#           ; '::.   ;\/\ /\ {
#          |.      ':. ;``"``\
#         / '::'::'    /      ;
#        |':::' '::'  /       |
#        \   '::' _.-`;       ;
#        /`-..--;` ;  |       |
#       ;  ;  ;  ;  ; |       |
#       ; ;  ;  ; ;  ;        /        ,--.........,
#       |; ;  ;  ;  ;/       ;       .'           -='.
#       | ;  ;  ; ; /       /       .\               '
#       |  ;   ;  /`      .\   _,=="  \             .'
#       \;  ; ; .'. _  ,_'\.\~"   //`. \          .'
#       |  ;  .___~' \ \- | |    /,\ `  \      ..'
#     ~ ; ; ;/  =="'' |`| | |       =="''\.==''
#     ~ /; ;/=""      |`| |`|   ==="`
#     ~..==`     \\   |`| / /=="`
#      ~` ~      /,\ / /= )")
#     ~ ~~         _')")
#     ~ ~   _,=~";`
#     ~  =~"|;  ;|       Penisbird
#      ~  ~ | ;  |       =========
#   ~ ~     |;|\ |
#           |/  \|

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
# THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import collections
import re
import discord
from discord.ext import commands
import asyncio
import unidecode
import random

#GAMER_REGEX = r'(?:[^s]|^)(n+\s*i+\s*g\s*g+\s*(?:e+\s*r+|(a)))(\s*s+)?'
GAMER_REGEX = r'(b+\s*r+\s*u+\s*h+)'

with open('data/catchphrases.txt') as f:
	CATCHPHRASES = list(map(str.rstrip, f))

class GamerWords(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.webhook_cache = collections.defaultdict(lambda: collections.defaultdict(list))
		# {guild:{channel:[webhook]}}
		bot.loop.create_task(self.populate_webhook_cache())
		bot.loop.create_task(self.clear_usernames())

	def has_gamer_words(self, string):
		string = unidecode.unidecode(string)
		match = re.search(GAMER_REGEX, string, flags=re.IGNORECASE)
		return match

	async def populate_webhook_cache(self):
		await self.bot.wait_until_ready()
		for guild in self.bot.guilds:
			for channel in guild.text_channels:
				try:
					webhooks = await channel.webhooks()
				except discord.HTTPException:
					continue

				for webhook in await channel.webhooks():
					if webhook.user == guild.me:
						self.webhook_cache[guild][webhook.channel].append(webhook)

	@commands.Cog.listener()
	async def on_webhooks_update(self, channel):
		webhooks = await channel.webhooks()
		webhooks = [webhook for webhook in webhooks if webhook.user == channel.guild.me]
		self.webhook_cache[channel.guild][channel] = webhooks

	async def get_webhook(self, channel):
		try:
			webhook = self.webhook_cache[channel.guild][channel][0]
			return webhook
		except (KeyError, IndexError):
			try:
				webhook = await channel.create_webhook(name='GamerHook')
				return webhook
			except discord.HTTPException:
				return None

	@commands.Cog.listener()
	async def on_message(self, message):
		if message.author.bot:
			return
		await self.handle_new_gamer_message(message)

	@commands.Cog.listener()
	async def on_message_edit(self, old_message, new_message):
		if old_message.author.bot:
			return
		await self.handle_new_gamer_message(new_message)

	async def handle_new_gamer_message(self, message):
		match = self.has_gamer_words(message.content)
		if match:
			try:
				await message.delete()
			except discord.HTTPException:
				return

			if not message.channel.permissions_for(message.guild.me).manage_webhooks:
				return

			webhook = await self.get_webhook(message.channel)
			if not webhook:
				return

			author = message.author
			new_content = self.censor_gamers(message.content)
			await webhook.send(
				content=new_content,
				username=author.display_name,
				avatar_url=str(author.avatar_url),
			)

	def censor_gamers(self, string):
		string = unidecode.unidecode(string)
		return re.sub(GAMER_REGEX, lambda _: random.choice(CATCHPHRASES), string, flags=re.IGNORECASE)

	async def clear_usernames(self):
		await self.bot.wait_until_ready()
		for guild in self.bot.guilds:
			if not guild.me.guild_permissions.manage_nicknames:
				continue

			for member in guild.members:
				if member.top_role > guild.me.top_role:
					continue

				match = self.has_gamer_words(member.display_name)
				if match:
					new_content = self.censor_gamers(member.display_name)
					await member.edit(nick=new_content)

	@commands.Cog.listener()
	async def on_member_update(self, old_member, new_member):
		if old_member.display_name == new_member.display_name:
			return
		if old_member.top_role > old_member.guild.me.top_role:
			return

		match = self.has_gamer_words(new_member.display_name)
		if match:
			new_content = self.censor_gamers(new_member.display_name)
			await new_member.edit(nick=new_content)

def setup(bot):
	bot.add_cog(GamerWords(bot))
