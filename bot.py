import os
from typing import Optional

from twitchio.ext.commands.errors import MissingRequiredArgument


def path_exists(filename):
    return os.path.join(".", f"{filename}")


if not os.path.exists(path_exists("config.json")):
    print("Config file not found. Exiting.\nPlease run `setup.py`")
    exit()

if not os.path.exists(path_exists(".env")):
    print("Environment Variables not found. Exiting.\nPlease run `setup.py`")
    exit()

if not os.path.exists(path_exists("blacklist.json")):
    print(
        "Blacklist file not found. Exiting.\nPlease run `setup.py`\n(or make a `blacklist.json` file yourself, if you know how to)\nhttps://github.com/mmattbtw/TwitchTunes/wiki/Blacklist.json"
    )
    exit()

if not os.path.exists(path_exists("blacklist_user.json")):
    print(
        "Blacklisted users file not found. Exiting.\nPlease run `setup.py`\n(or make a `blacklist_user.json` file yourself, if you know how to)\nhttps://github.com/mmattbtw/TwitchTunes/wiki/Blacklist.json"
    )
    exit()

if not os.path.exists(path_exists("authroles.json")):
    print(
        "Blacklisted users file not found. Exiting.\nPlease run `setup.py`\n(or make a `authroles.json` file yourself, if you know how to)\nhttps://github.com/mmattbtw/TwitchTunes/wiki/Blacklist.json"
    )
    exit()


os.system("pip install -U -r requirements.txt")
print("\n\nStarting 🎶TwitchTunes")

from aiohttp import request
from pathlib import Path

from twitchio.ext import commands
from twitchio.ext import pubsub

import dotenv

cwd = Path(__file__).parents[0]
cwd = str(cwd)
import asyncio

import json

import re

import spotipy
from spotipy.oauth2 import SpotifyOAuth

URL_REGEX = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

with open("config.json") as config_file:
    config = json.load(config_file)

dotenv.load_dotenv()

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.environ.get("spotify_client_id"),
        client_secret=os.environ.get("spotify_secret"),
        redirect_uri="http://localhost:8080",
        scope=[
            "user-modify-playback-state",
            "user-read-currently-playing",
            "user-read-playback-state",
        ],
    )
)


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=os.environ.get("TOKEN"),
            client_id=os.environ.get("client_id"),
            nick=config["nickname"],
            prefix=config["prefix"],
            initial_channels=config["channels"],
        )

        self.token = os.environ.get("SPOTIFY_AUTH")
        self.version = "1.2.6"

    async def event_ready(self):
        print("\n" * 100)
        print(f"TwitchTunes ({self.version}) Ready, logged in as: {self.nick}")
        print(
            "Ignore the 'AttributeError: 'NoneType' object has no attribute '_ws'' error, this is an issue with the library."
        )

    def read_json(self, filename):
        with open(f"{filename}.json", "r") as file:
            data = json.load(file)
        return data
    async def checkrole(ctx):
        with open("authroles.json","r") as authroles:
            authr = json.load(authroles)
            for role in ctx.author.roles:
                if role.id in authr["roles"]:
                    await ctx.send("You are blacklisted")
                    return False
         return True
    def write_json(self, data, filename):
        with open(f"{filename}.json", "w") as file:
            json.dump(data, file, indent=4)

    def is_owner(self, ctx):
        return ctx.author.id == "640348450"

    async def event_message(self, message):
        await self.handle_commands(message)

    # This is an owner only command for an inside joke in a certain channel, just ignore this :)
    @commands.command(name="S3S")
    @commands.check(checkrole)
    async def s3s(self, ctx):
        if self.is_owner(ctx) and ctx.channel.name == "tajj":
            same_3_songs = [
                "spotify:track:7jVH8CXr0MSpGheHOjN4NA",
                "spotify:track:0BRbI3ZMPXuj9yA7ChDGOW",
                "spotify:track:0S8pAna5CIUy0g9XM5hBeF",
            ]
            for song in same_3_songs:
                sp.add_to_queue(song)
                await asyncio.sleep(0.1)
            await ctx.send("forsenPls same 3 songs forsenPls")
            
    @commands.command((name="roleadd")
    async def add_bl_role(self,ctx,role):
        role = role.replace("<@","")
        role = role.replace(">","")
        try:
             int(role)
        except:
             return await ctx.send("Please enter a valid role/ role id")
        with open("authroles.json","r") as authroles:
            authr = json.load(authroles)
        authr["roles"].append(role)
        with open("authroles.json","w") as authroles:
            json.dump(authr,authroles)
        await ctx.send(f"Sucessfully blacklisted {role}")
                      
    @commands.command((name="roleremove")
    async def remove_bl_role(self,ctx,role):
        role = role.replace("<@","")
        role = role.replace(">","")
        with open("authroles.json","r") as authroles:
            authr = json.load(authroles)
        if role not in authr["roles"]:
            return await ctx.send("Role not blacklisted")
        authr["roles"].remove(role)
        with open("authroles.json","w") as authroles:
            json.dump(authr,authroles)
        await ctx.send(f"Sucessfully unblacklisted {role}")
                      
    @commands.command(name="ping", aliases=["ding"])
    @commands.check(checkrole)
    async def ping_command(self, ctx):
        await ctx.send(
            f":) 🎶 TwitchTunes v{self.version} (Spotify Song Requests) is online!"
        )

    @commands.command(name="blacklistuser")
    @commands.check(checkrole)
    async def blacklist_user(self, ctx, *, user: str):
        user = user.lower()
        if ctx.author.is_mod or self.is_owner(ctx):
            file = self.read_json("blacklist_user")
            if user not in file["users"]:
                file["users"].append(user)
                self.write_json(file, "blacklist_user")
                await ctx.send(f"{user} added to blacklist")
            else:
                await ctx.send(f"{user} is already blacklisted")
        else:
            await ctx.send("You don't have permission to do that.")

    @commands.command(name="unblacklistuser")
    @commands.check(checkrole)
    async def unblacklist_user(self, ctx, *, user: str):
        user = user.lower()
        if ctx.author.is_mod or self.is_owner(ctx):
            file = self.read_json("blacklist_user")
            if user in file["users"]:
                file["users"].remove(user)
                self.write_json(file, "blacklist_user")
                await ctx.send(f"{user} removed from blacklist")
            else:
                await ctx.send(f"{user} is not blacklisted")
        else:
            await ctx.send("You don't have permission to do that.")

    @commands.command(name="blacklist", aliases=["blacklistsong", "blacklistadd"])
    @commands.check(checkrole)
    async def blacklist_command(self, ctx, *, song_uri: str):
        if ctx.author.is_mod or self.is_owner(ctx):
            jscon = self.read_json("blacklist")

            song_uri = song_uri.replace("spotify:track:", "")

            if song_uri not in jscon["blacklist"]:
                if re.match(URL_REGEX, song_uri):
                    data = sp.track(song_uri)
                    song_uri = data["uri"]
                    song_uri = song_uri.replace("spotify:track:", "")

                track = sp.track(song_uri)

                track_name = track["name"]

                jscon["blacklist"].append(song_uri)

                self.write_json(jscon, "blacklist")

                await ctx.send(f"Added {track_name} to blacklist.")

            else:
                await ctx.send(f"Song is already blacklisted.")

        else:
            await ctx.send("You are not authorized to use this command.")

    @commands.command(
        name="unblacklist", aliases=["unblacklistsong", "blacklistremove"]
    )
    @commands.check(checkrole)
    async def unblacklist_command(self, ctx, *, song_uri: str):
        if ctx.author.is_mod or self.is_owner(ctx):
            jscon = self.read_json("blacklist")

            song_uri = song_uri.replace("spotify:track:", "")

            if re.match(URL_REGEX, song_uri):
                data = sp.track(song_uri)
                song_uri = data["uri"]
                song_uri = song_uri.replace("spotify:track:", "")

            if song_uri in jscon["blacklist"]:
                jscon["blacklist"].remove(song_uri)
                self.write_json(jscon, "blacklist")
                await ctx.send(f"Removed that song from the blacklist.")

            else:
                await ctx.send(f"Song is not blacklisted.")
        else:
            await ctx.send("You are not authorized to use this command.")

    @commands.command(name="np", aliases=["nowplaying", "song"])
    @commands.check(checkrole)
    async def np_command(self, ctx):
        data = sp.currently_playing()
        song_artists = data["item"]["artists"]
        song_artists_names = [artist["name"] for artist in song_artists]

        min_through = int(data["progress_ms"] / (1000 * 60) % 60)
        sec_through = int(data["progress_ms"] / (1000) % 60)
        time_through = f"{min_through} mins, {sec_through} secs"

        min_total = int(data["item"]["duration_ms"] / (1000 * 60) % 60)
        sec_total = int(data["item"]["duration_ms"] / (1000) % 60)
        time_total = f"{min_total} mins, {sec_total} secs"

        await ctx.send(
            f"🎶Now Playing - {data['item']['name']} by {', '.join(song_artists_names)} | Link: {data['item']['external_urls']['spotify']} | {time_through} - {time_total}"
        )

    @commands.command(name="songrequest", aliases=["sr", "addsong"])
    @commands.check(checkrole)
    async def songrequest_command(self, ctx, *, song: str):
        song_uri = None

        if (
            song.startswith("spotify:track:")
            or not song.startswith("spotify:track:")
            and re.match(URL_REGEX, song)
        ):
            song_uri = song
            await self.song_request(ctx, song_uri, song_uri, album=False)

        else:
            await self.song_request(ctx, song, song_uri, album=False)

    # @commands.command(name="skip")
    # async def skip_song_command(self, ctx):
    #     sp.next_track()
    #     await ctx.send(f":) 🎶 Skipping song...")

    # @commands.command(name="albumqueue")
    #     if ctx.author.is_mod or ctx.author.is_subscriber or self.is_owner(ctx):
    # async def albumqueue_command(self, ctx, *, album: str):
    #         album_uri = None

    #         if (
    #             album.startswith("spotify:album:")
    #             or not album.startswith("spotify:album:")
    #             and re.match(URL_REGEX, album)
    #         ):
    #             album_uri = album
    #         await self.album_request(ctx, album_uri)
    #     else:
    #         await ctx.send(f"🎶You don't have permission to do that! (Album queue is Sub Only!)")

    # async def album_request(self, ctx, song):
    #     song = song.replace("spotify:album:", "")
    #     ALBUM_URL = f"https://api.spotify.com/v1/albums/{song}?market=US"
    #     async with request("GET", ALBUM_URL, headers={
    #                 "Content-Type": "application/json",
    #                 "Authorization": "Bearer " + self.token,
    #             }) as resp:
    #             data = await resp.json()
    #             songs_uris = [artist["uri"] for artist in data['tracks']['items']]

    #             for song_uris in songs_uris:
    #                 await self.song_request(ctx, song, song_uris, album=True)
    #             await ctx.send(f"Album Requested! {data['name']}")
    #             return

    async def song_request(self, ctx, song, song_uri, album: bool):
        blacklisted_users = self.read_json("blacklist_user")["users"]
        if ctx.author.name.lower() in blacklisted_users:
            await ctx.send("You are blacklisted from requesting songs.")
        else:
            jscon = self.read_json("blacklist")

            if song_uri is None:
                data = sp.search(song, limit=1, type="track", market="US")
                song_uri = data["tracks"]["items"][0]["uri"]

            elif re.match(URL_REGEX, song_uri):
                data = sp.track(song_uri)
                song_uri = data["uri"]
                song_uri = song_uri.replace("spotify:track:", "")

            song_id = song_uri.replace("spotify:track:", "")

            if not album:
                data = sp.track(song_id)
                song_name = data["name"]
                song_artists = data["artists"]
                song_artists_names = [artist["name"] for artist in song_artists]
                duration = data["duration_ms"] / 60000

            if song_uri != "not found":
                if song_id in jscon["blacklist"]:
                    await ctx.send("That song is blacklisted.")

                elif duration > 17:
                    await ctx.send("Send a shorter song please! :)")
                else:
                    sp.add_to_queue(song_uri)
                    await ctx.send(
                        f"@{ctx.author.name}, Your song ({song_name} by {', '.join(song_artists_names)}) [ {data['external_urls']['spotify']} ] has been added to the queue!"
                    )


bot = Bot()
bot.run()
