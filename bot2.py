import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================
# CONFIG – ΒΑΛΕ ΤΑ ΔΙΚΑ ΣΟΥ IDs
# ==========================

GUILD_ID = 1465344517090840639

LOGS_CHANNEL_ID = 1465370236243939379

AUTOROLE_ID = 1465357638593151331

SUPPORT_TICKET_CATEGORY_ID = 1465366628622667830
BUY_TICKET_CATEGORY_ID = 1465375930321997986
APPLICATION_CATEGORY_ID = 1465726366229205043

SUPPORT_CALL_VC_ID = 1465366816959234109
TEMP_SUPPORT_CATEGORY_ID = 1465366473030635788

OWNER_ROLE_ID = 1465345430392017091
CEO_ROLE_ID = 1465362545668788320
MANAGER_ROLE_ID = 1465360458537111582
STAFF_ROLE_ID = 1467220345126654185
WAITING_FOR_INTERVIEW_ROLE_ID = 1465728338772623413

# ==========================
# HELPERS
# ==========================

def has_role(member: discord.Member, role_id: int) -> bool:
    role = member.guild.get_role(role_id)
    return role in member.roles if role else False

def is_owner_or_ceo(member: discord.Member) -> bool:
    return has_role(member, OWNER_ROLE_ID) or has_role(member, CEO_ROLE_ID)

def is_staff_or_higher(member: discord.Member) -> bool:
    return any([
        has_role(member, STAFF_ROLE_ID),
        has_role(member, MANAGER_ROLE_ID),
        has_role(member, CEO_ROLE_ID),
        has_role(member, OWNER_ROLE_ID),
    ])

def is_manager_or_higher(member: discord.Member) -> bool:
    return any([
        has_role(member, MANAGER_ROLE_ID),
        has_role(member, CEO_ROLE_ID),
        has_role(member, OWNER_ROLE_ID),
    ])

def get_logs_channel(guild: discord.Guild):
    return guild.get_channel(LOGS_CHANNEL_ID)

# ==========================
# EVENTS – READY / AUTOROLE / WELCOME / LEAVE
# ==========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_member_join(member: discord.Member):
    role = member.guild.get_role(AUTOROLE_ID)
    if role:
        try:
            await member.add_roles(role)
        except:
            pass

    logs = get_logs_channel(member.guild)
    if logs:
        embed = discord.Embed(
            title="Member Joined",
            description=f"{member.mention} μπήκε στον server.",
            color=discord.Color.green()
        )
        await logs.send(embed=embed)

@bot.event
async def on_member_remove(member: discord.Member):
    logs = get_logs_channel(member.guild)
    if logs:
        embed = discord.Embed(
            title="Member Left",
            description=f"{member} βγήκε από τον server.",
            color=discord.Color.red()
        )
        await logs.send(embed=embed)

# ==========================
# LOGS – MESSAGES / CHANNELS / ROLES / VOICE / BANS
# ==========================

@bot.event
async def on_message_delete(message: discord.Message):
    if not message.guild or message.author.bot:
        return
    logs = get_logs_channel(message.guild)
    if logs:
        embed = discord.Embed(
            title="Message Deleted",
            color=discord.Color.red()
        )
        embed.add_field(name="User", value=f"{message.author}", inline=False)
        embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        embed.add_field(name="Content", value=message.content or "No content", inline=False)
        await logs.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if not after.guild or after.author.bot:
        return
    if before.content == after.content:
        return
    logs = get_logs_channel(after.guild)
    if logs:
        embed = discord.Embed(
            title="Message Edited",
            color=discord.Color.yellow()
        )
        embed.add_field(name="User", value=f"{after.author}", inline=False)
        embed.add_field(name="Before", value=before.content or "No content", inline=False)
        embed.add_field(name="After", value=after.content or "No content", inline=False)
        await logs.send(embed=embed)

# ==========================
# TEMPORARY SUPPORT CALL
# ==========================

@bot.event
async def on_voice_state_update(member, before, after):
    logs = get_logs_channel(member.guild)

    # Log voice events
    if logs:
        if not before.channel and after.channel:
            await logs.send(embed=discord.Embed(
                title="Voice Join",
                description=f"{member.mention} μπήκε στο {after.channel.mention}",
                color=discord.Color.blue()
            ))
        elif before.channel and not after.channel:
            await logs.send(embed=discord.Embed(
                title="Voice Leave",
                description=f"{member.mention} βγήκε από {before.channel.mention}",
                color=discord.Color.red()
            ))
        elif before.channel and after.channel and before.channel.id != after.channel.id:
            await logs.send(embed=discord.Embed(
                title="Voice Move",
                description=f"{member.mention} μετακινήθηκε από {before.channel.mention} σε {after.channel.mention}",
                color=discord.Color.yellow()
            ))

    # TEMP SUPPORT CALL CREATION
    try:
        if after.channel and after.channel.id == SUPPORT_CALL_VC_ID:
            guild = member.guild
            category = guild.get_channel(TEMP_SUPPORT_CATEGORY_ID)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
                member: discord.PermissionOverwrite(view_channel=True, connect=True),
                guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, connect=True),
                guild.get_role(MANAGER_ROLE_ID): discord.PermissionOverwrite(view_channel=True, connect=True),
                guild.get_role(CEO_ROLE_ID): discord.PermissionOverwrite(view_channel=True, connect=True),
                guild.get_role(OWNER_ROLE_ID): discord.PermissionOverwrite(view_channel=True, connect=True),
            }

            temp_channel = await guild.create_voice_channel(
                name=f"support-{member.name}",
                category=category,
                overwrites=overwrites,
                reason="Temporary support call"
            )

            await member.move_to(temp_channel)

            async def delete_when_empty():
                await asyncio.sleep(5)
                while True:
                    ch = guild.get_channel(temp_channel.id)
                    if not ch or len(ch.members) == 0:
                        try:
                            await ch.delete(reason="Temp support call empty")
                        except:
                            pass
                        break
                    await asyncio.sleep(10)

            bot.loop.create_task(delete_when_empty())

    except Exception as e:
        print("Temp call error:", e)

# ==========================
# TICKET CLOSE BUTTON
# ==========================

class TicketCloseView(discord.ui.View):
    def init(self):
        super().init(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction, button):
        if not is_staff_or_higher(interaction.user):
            return await interaction.response.send_message("Δεν έχεις δικαίωμα.", ephemeral=True)

        await interaction.response.send_message("Το ticket θα κλείσει σε 5 δευτερόλεπτα...", ephemeral=True)
        await asyncio.sleep(5)

        try:
            await interaction.channel.delete(reason="Ticket closed")
        except:
            pass

# ==========================
# TICKET CREATION FUNCTION
# ==========================

async def create_ticket(interaction, ticket_type, category_id, allowed_roles):
    guild = interaction.guild
    category = guild.get_channel(category_id)

# ==========================
# APPLICATION PANELS
# ==========================

class StaffApplicationPanel(discord.ui.View):
    def init(self):
        super().init(timeout=None)

    @discord.ui.button(label="Apply for Staff", style=discord.ButtonStyle.primary)
    async def apply_staff(self, interaction, button):
        modal = StaffApplicationModal()
        await interaction.response.send_modal(modal)


class ManagerApplicationPanel(discord.ui.View):
    def init(self):
        super().init(timeout=None)

    @discord.ui.button(label="Apply for Manager", style=discord.ButtonStyle.danger)
    async def apply_manager(self, interaction, button):
        modal = ManagerApplicationModal()
        await interaction.response.send_modal(modal)


# ==========================
# STAFF APPLICATION MODAL
# ==========================

class StaffApplicationModal(discord.ui.Modal, title="Staff Application"):

    q1 = discord.ui.TextInput(label="Πόσο χρονών είσαι;", style=discord.TextStyle.short)
    q2 = discord.ui.TextInput(label="Πόσες ώρες θα μπορείς να είσαι on duty την μέρα;", style=discord.TextStyle.short)
    q3 = discord.ui.TextInput(label="Τι είναι η ιεραρχία για σένα;", style=discord.TextStyle.paragraph)
    q4 = discord.ui.TextInput(label="Έχεις εμπειρία πάνω στο staff κομμάτι;", style=discord.TextStyle.paragraph)
    q5 = discord.ui.TextInput(label="Πες 3 βασικά rules του server", style=discord.TextStyle.paragraph)
    q6 = discord.ui.TextInput(label="Τι θα κάνεις δεν μπορείς να βοηθήσεις κάποιον στο support/ticket;", style=discord.TextStyle.paragraph)
    q7 = discord.ui.TextInput(label="Πως θα αντιδράσεις αν κάποιο άλλο μέλος από το staff team έχει αντιεπαγγελματική συμπεριφορά;", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction):
        guild = interaction.guild
        category = guild.get_channel(APPLICATION_CATEGORY_ID)

        channel = await guild.create_text_channel(
            name=f"staff-app-{interaction.user.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.get_role(OWNER_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.get_role(CEO_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
        )

        embed = discord.Embed(title="Νέα Staff Αίτηση", color=discord.Color.blue())
        embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
        embed.add_field(name="Πόσο χρονών είσαι;", value=self.q1.value, inline=False)
        embed.add_field(name="Ώρες on duty", value=self.q2.value, inline=False)
        embed.add_field(name="Τι είναι η ιεραρχία;", value=self.q3.value, inline=False)
        embed.add_field(name="Εμπειρία staff", value=self.q4.value, inline=False)
        embed.add_field(name="3 βασικά rules", value=self.q5.value, inline=False)
        embed.add_field(name="Αν δεν μπορείς να βοηθήσεις", value=self.q6.value, inline=False)
        embed.add_field(name="Αντιεπαγγελματική συμπεριφορά staff", value=self.q7.value, inline=False)

        await channel.send(embed=embed, view=ApplicationDecisionView(interaction.user.id))
        await interaction.response.send_message("Η αίτησή σου στάλθηκε!", ephemeral=True)


# ==========================
# MANAGER APPLICATION MODAL
# ==========================

class ManagerApplicationModal(discord.ui.Modal, title="Manager Application"):

    q1 = discord.ui.TextInput(label="Πόσο χρονών είσαι;", style=discord.TextStyle.short)
    q2 = discord.ui.TextInput(label="Πόσες ώρες θα μπορείς να είσαι on duty την ημέρα;", style=discord.TextStyle.short)
    q3 = discord.ui.TextInput(label="Ανέφερε 3 βασικά rules του server", style=discord.TextStyle.paragraph)
    q4 = discord.ui.TextInput(label="Τι είναι η ιεραρχία για σένα;", style=discord.TextStyle.paragraph)
    q5 = discord.ui.TextInput(label="Έχεις εμπειρία πάνω στο κομμάτι management;", style=discord.TextStyle.paragraph)
    q6 = discord.ui.TextInput(label="Πως θα αντιμετώπιζες μια δύσκολη σύγκρουση στο team;", style=discord.TextStyle.paragraph)
    q7 = discord.ui.TextInput(label="Τι θα έκανες αν κάποιος δεν άκουγε τις εντολές σου;", style=discord.TextStyle.paragraph)
    q8 = discord.ui.TextInput(label="Τι θα έκανες αν δεν σου αρέσει εντολή ανώτερου;", style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction):
        guild = interaction.guild
        category = guild.get_channel(APPLICATION_CATEGORY_ID)

        channel = await guild.create_text_channel(
            name=f"manager-app-{interaction.user.name}",
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.get_role(OWNER_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
                guild.get_role(CEO_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
        )

        embed = discord.Embed(title="Νέα Manager Αίτηση", color=discord.Color.green())
        embed.add_field(name="User", value=f"{interaction.user} ({interaction.user.id})", inline=False)
        embed.add_field(name="Πόσο χρονών είσαι;", value=self.q1.value, inline=False)
        embed.add_field(name="Ώρες on duty", value=self.q2.value, inline=False)
        embed.add_field(name="3 βασικά rules", value=self.q3.value, inline=False)
        embed.add_field(name="Τι είναι η ιεραρχία;", value=self.q4.value, inline=False)
        embed.add_field(name="Εμπειρία management", value=self.q5.value, inline=False)
        embed.add_field(name="Αντιμετώπιση σύγκρουσης", value=self.q6.value, inline=False)
        embed.add_field(name="Αν δεν ακούει εντολές", value=self.q7.value, inline=False)
        embed.add_field(name="Αν δεν σου αρέσει εντολή ανώτερου", value=self.q8.value, inline=False)

        await channel.send(embed=embed, view=ApplicationDecisionView(interaction.user.id))
        await interaction.response.send_message("Η αίτησή σου στάλθηκε!", ephemeral=True)


# ==========================
# ACCEPT / DENY BUTTONS
# ==========================

class ApplicationDecisionView(discord.ui.View):
    def init(self, user_id):
        super().init(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="Accept with reason", style=discord.ButtonStyle.success)
    async def accept(self, interaction, button):
        if not is_owner_or_ceo(interaction.user):
            return await interaction.response.send_message("Δεν έχεις δικαίωμα.", ephemeral=True)

        modal = AcceptModal(self.user_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Denied with reason", style=discord.ButtonStyle.danger)
    async def deny(self, interaction, button):
        if not is_owner_or_ceo(interaction.user):
            return await interaction.response.send_message("Δεν έχεις δικαίωμα.", ephemeral=True)
        
    # ==========================
# SEND PANELS COMMAND
# ==========================

@bot.command()
async def send(ctx, panel_type=None, panel_name=None):
    if panel_type is None or panel_name is None:
        return await ctx.reply(
            "Χρησιμοποίησε:\n"
            "`!send support panel`\n"
            "`!send buy panel`\n"
            "`!send staff panel`\n"
            "`!send managers panel`"
        )

    panel_type = panel_type.lower()
    panel_name = panel_name.lower()

    # SUPPORT PANEL
    if panel_type == "support" and panel_name == "panel":
        if not is_staff_or_higher(ctx.author):
            return await ctx.reply("Δεν έχεις δικαίωμα.")
        embed = discord.Embed(
            title="Support Ticket",
            description="Επίλεξε τι ticket θέλεις να ανοίξεις.",
            color=discord.Color.blue()
        )
        return await ctx.send(embed=embed, view=SupportTicket())

    # BUY PANEL
    if panel_type == "buy" and panel_name == "panel":
        if not is_staff_or_higher(ctx.author):
            return await ctx.reply("Δεν έχεις δικαίωμα.")
        embed = discord.Embed(
            title="Buy Ticket",
            description="Επίλεξε τι θέλεις να κάνεις.",
            color=discord.Color.green()
        )
        return await ctx.send(embed=embed, view=BuyTicket())

    # STAFF APPLICATION PANEL
    if panel_type == "staff" and panel_name == "panel":
        if not is_owner_or_ceo(ctx.author):
            return await ctx.reply("Μόνο Owner/CEO.")
        embed = discord.Embed(
            title="Staff Application Panel",
            description="Πατήστε το κουμπί για να κάνετε αίτηση Staff.",
            color=discord.Color.blue()
        )
        return await ctx.send(embed=embed, view=StaffApplicationPanel())

    # MANAGERS APPLICATION PANEL
    if panel_type == "managers" and panel_name == "panel":
        if not is_owner_or_ceo(ctx.author):
            return await ctx.reply("Μόνο Owner/CEO.")
        embed = discord.Embed(
            title="Managers Application Panel",
            description="Πατήστε το κουμπί για να κάνετε αίτηση Manager.",
            color=discord.Color.green()
        )
        return await ctx.send(embed=embed, view=ManagerApplicationPanel())

    await ctx.reply("Λάθος χρήση εντολής.")


# ==========================
# SAY COMMAND
# ==========================

@bot.command()
async def say(ctx, *, text=None):
    if not is_staff_or_higher(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα.")
    if not text:
        return await ctx.reply("Γράψε τι να πω.")
    try:
        await ctx.message.delete()
    except:
        pass
    await ctx.send(text)


# ==========================
# DMALL COMMAND
# ==========================

@bot.command()
async def dmall(ctx, *, text=None):
    if not is_owner_or_ceo(ctx.author):
        return await ctx.reply("Μόνο Owner/CEO.")
    if not text:
        return await ctx.reply("Γράψε μήνυμα.")
    await ctx.reply("Ξεκινάω να στέλνω DM…")

    async for member in ctx.guild.fetch_members(limit=None):
        if member.bot:
            continue
        try:
            await member.send(text)
        except:
            pass


# ==========================
# MODERATION COMMANDS
# ==========================

@bot.command()
async def kick(ctx, member: discord.Member=None, *, reason=None):
    if not is_staff_or_higher(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα.")
    if member is None:
        return await ctx.reply("Κάνε mention τον χρήστη.")
    if reason is None:
        return await ctx.reply("Γράψε reason.")
    try:
        await member.kick(reason=reason)
        await ctx.reply(f"Kick: {member.mention} | Reason: {reason}")
    except:
        await ctx.reply("Δεν μπόρεσα να κάνω kick.")


@bot.command()
async def ban(ctx, member: discord.Member=None, *, reason=None):
    if not is_staff_or_higher(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα.")
    if member is None:
        return await ctx.reply("Κάνε mention τον χρήστη.")
    if reason is None:
        return await ctx.reply("Γράψε reason.")
    try:
        await member.ban(reason=reason)
        await ctx.reply(f"Ban: {member.mention} | Reason: {reason}")
    except:
        await ctx.reply("Δεν μπόρεσα να κάνω ban.")


@bot.command()
async def unban(ctx, user_id: int=None, *, reason=None):
    if not is_staff_or_higher(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα.")
    if user_id is None:
        return await ctx.reply("Γράψε user ID.")
    if reason is None:
        return await ctx.reply("Γράψε reason.")
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
        await ctx.reply(f"Unban: {user} | Reason: {reason}")
    except:
        await ctx.reply("Δεν μπόρεσα να κάνω unban.")


@bot.command()
async def timeout(ctx, member: discord.Member=None, minutes: int=None, *, reason=None):
    if not is_staff_or_higher(ctx.author):
        return await ctx.reply("Δεν έχεις δικαίωμα.")
    if member is None:
        return await ctx.reply("Κάνε mention.")
    if minutes is None:
        return await ctx.reply("Γράψε λεπτά.")
    if reason is None:
        return await ctx.reply("Γράψε reason.")

    try:
        until = discord.utils.utcnow() + discord.timedelta(minutes=minutes)
        await member.edit(timeout=until, reason=reason)
        await ctx.reply(f"Timeout: {member.mention} για {minutes} λεπτά | Reason: {reason}")
    except:
        await ctx.reply("Δεν μπόρεσα να κάνω timeout.")


# ==========================
# BOT PANEL
# ==========================

@bot.command()
async def botpanel(ctx):
    embed = discord.Embed(
        title="Bot Panel",
        color=discord.Color.purple()
    )
    embed.add_field(name="General", value="!say, !dmall", inline=False)
    embed.add_field(name="Tickets", value="!send support ticket, !send buy ticket", inline=False)
    embed.add_field(name="Applications", value="!send staff panel, !send managers panel", inline=False)
    embed.add_field(name="Moderation", value="!kick, !ban, !unban, !timeout", inline=False)
    await ctx.send(embed=embed)


# ==========================
# RUN BOT
# ==========================

bot.run("PUT_YOUR_TOKEN_HERE")