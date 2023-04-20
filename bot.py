import json, os, time, json, sys, logging, asyncio,datetime

import discord
from discord.ext import commands
from discord import app_commands

from nicelog.formatters import Colorful

from libs import sql, components


logger = logging.getLogger('sql')
logger.setLevel(logging.DEBUG,)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(Colorful(
                                message_inline=True, 
                                show_filename=False, 
                                show_function=False
                              ))
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


config = json.loads(open("config.json","r", encoding="utf8").read())


class Cooldown:
    def __init__(self, duration):

        self.duration = duration
        self.last_end_time = None

    def remaining_time(self):
        if self.last_end_time is None:
            return 0
        else:
            return max(self.last_end_time - time.time(), 0)
    def start(self):
        self.last_end_time = time.time() + self.duration
    def is_on_cooldown(self):
        return self.remaining_time() > 0





class Discord_Bot:

    bot = None

    def __init__(self) -> None:


        self.bot_prefix = config['bot_config']["prefix"]
        self.bot_token = config['bot_config']["token"]
        self.server_id = config['bot_config']["server_id"]

        self.cooldown = {}
        
        os.system("cls")

        self.db = sql.Database(logger=logger)
        self.run_bot()
        

    def get_dashboard(self, user_id):

        user_data = self.db.get_key(discord_id=str(user_id))


        if user_data == False:
            
            description= "```There is no active license for your account```"
        
            embed = discord.Embed(
                title=f"User panel",
                description=description
                )
            embed.set_image(url="https://cdn.discordapp.com/attachments/1098670145972469770/1098672935318847548/excer.png")
            return embed
        
        else:
            user_data = user_data[0]

            if round(time.time()) < user_data[1]:
                time_left = components.time_left(user_data[1])
            else:
                time_left = "Expired"

            hwid_info = "{}/{}".format(len(json.loads(user_data[4])), user_data[5])
            description = "\u200b"
            description += "\n```⏰│ time > {}\n🔑│ key > {}\n💻│ hwid > {}```".format(time_left, user_data[2], hwid_info)
            description += "▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁▁"

            embed = discord.Embed(
                title=f"`User panel`",
                description=description
                )
            return embed
        

    def commands(self):

        @self.bot.event
        async def on_ready():
            await self.tree.sync(guild=discord.Object(id=self.server_id))
            await self.bot.change_presence(activity=discord.Game(name=f"ExcerAuth"))


        @self.tree.command(name="claim",description="[LICENSE] Claim your license", guild=discord.Object(id=self.server_id))
        async def claim(interaction, license: str):
            
            discord_id=str(interaction.user.id)

            res = self.db.change_owner(license=license, discord_id=discord_id)
            if res['success'] == True:
                embed = discord.Embed(
                    description="```LICENSE CLAIMED```"
                    )
                embed.set_image(url="https://cdn.discordapp.com/attachments/1098670145972469770/1098672935318847548/excer.png")
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(
                    description="```INVALID LICENSE```"
                    )
                embed.set_image(url="https://cdn.discordapp.com/attachments/1098670145972469770/1098672935318847548/excer.png")
                await interaction.response.send_message(embed=embed)




        @self.tree.command(name="panel",description="[PANEL] User panel", guild=discord.Object(id=self.server_id))
        async def panel(interaction):
            
            discord_id=str(interaction.user.id)

            if not discord_id in self.cooldown:
                self.cooldown[discord_id] = [   
                    Cooldown(600),
                    Cooldown(120)                    
                        ]

            get_dashboard = lambda user : self.get_dashboard(user)

            def cooldown(i):
                self.cooldown[discord_id]
                if not self.cooldown[discord_id][i].is_on_cooldown():
                    self.cooldown[discord_id][i].start()
                    return True
                else:
                    return round(self.cooldown[discord_id][i].remaining_time() / 60)



            def db_reset_hwid(discord_id):
                res = self.db.reset_hwid(discord_id=discord_id)

            def db_reset_key(discord_id):
                res = self.db.reset_key(discord_id=discord_id)


            class Static(discord.ui.View):

                @discord.ui.button(label='Reset hwid', style=discord.ButtonStyle.grey,row=1, emoji="💻")
                async def reset_hwid(self, interaction1: discord.Interaction, button: discord.ui.Button):
                    cooldown_check = cooldown(0)
                    if cooldown_check == True:
                        db_reset_hwid(discord_id)
                        await interaction1.response.edit_message(embed=get_dashboard(discord_id))
                    else:
                        mess = await interaction1.channel.send("```COOLDOWN: {}m```".format(cooldown_check))
                        await asyncio.sleep(3)
                        try:
                            await mess.delete()
                        except:
                            pass

                @discord.ui.button(label='Reset key', style=discord.ButtonStyle.grey,row=1, emoji="🔐")
                async def reset_key(self, interaction1: discord.Interaction, button: discord.ui.Button):
                    cooldown_check = cooldown(1)
                    if cooldown_check == True:
                        db_reset_key(discord_id)
                        await interaction1.response.edit_message(embed=get_dashboard(discord_id))
                    else:
                        mess = await interaction1.channel.send("```COOLDOWN: {}m```".format(cooldown_check))
                        await asyncio.sleep(3)
                        try:
                            await mess.delete()
                        except:
                            pass

            view = Static()
            embed = self.get_dashboard(interaction.user.id)
            res = self.db.get_key(discord_id=discord_id)
            if res != False:
                await interaction.response.send_message(embed=embed, view=view)
            else:
                await interaction.response.send_message(embed=embed)



        @self.tree.command(name="create",description="[ADMIN] Create license", guild=discord.Object(id=self.server_id))
        async def create(interaction, license_time: str, hwid_limit: int = 1):
            role = discord.utils.get(interaction.guild.roles, id=config['bot_config']['admin_role'])
            if role in interaction.user.roles:

                time_prefix = str(license_time[len(license_time)-1])
                
                if (time_prefix == "h") or (time_prefix == "d"):
                    try: 
                        int(license_time[:-1])
                    except:
                        embed = discord.Embed( description=f"```**INVALID**\n\n> Valid usage: `30h` / `30d`")
                        await interaction.response.send_message(embed=embed)

                    data_dict = {
                        "type":time_prefix,
                        "val":int(license_time[:-1])
                    }
                    res = self.db.add_user(0,data_dict, hwid_limit)
                    await interaction.response.send_message("CREATED KEY: ||{}||".format(res))

                else:
                    embed = discord.Embed( description=f"```**INVALID**\n\n> Valid usage: `30h` / `30d`")
                    await interaction.response.send_message(embed=embed)
                    return
                
                return
            

    def run_bot(self):

        self.bot = discord.Client(
            command_prefix=self.bot_prefix, 
            help_command=None, 
            intents=discord.Intents().all()
        )

        self.tree = app_commands.CommandTree(self.bot)
        self.commands()
        self.bot.run(self.bot_token)
        


if __name__ == "__main__":

    Discord_Bot()
