# This file is part of the OE-A distribution (https://github.com/xxxx or http://xxx.github.io).
# Copyright (c) 2015 Liviu Ionescu.
# 
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Special thanks go to @jbleyel who was and is significantly involved in the realization.

# -*- coding: UTF-8 -*-
import base64
from os import mkdir
from os.path import exists, join
from json import loads
import re
import requests
#from PIL import Image

from enigma import eServiceReference, ePicLoad, gPixmapPtr

from Components.ActionMap import ActionMap
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Plugins.Plugin import PluginDescriptor
from Screens.InfoBar import MoviePlayer
from Screens.Screen import Screen
from twisted.internet.reactor import callInThread
PLUGINPATH = "/usr/lib/enigma2/python/Plugins/Extensions/EnigmaWelt/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36"
TMPIC = "/tmp/ewcover"


def geturl(url):
	try:
		r = requests.get(url, timeout=10, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-us,en;q=0.9,de-DE,de;q=0.8", "Accept-Encoding": "gzip, deflate"})
		r.raise_for_status()
		return r.content
	except requests.RequestException:
		return ""


class enimaWeltScreen(Screen):

	skin = """
	<screen name="Main" position="center,center" size="1200,600" resolution="1280,720" flags="wfNoBorder" >
		<widget source="Title" render="Label" position="10,5" size="1150,40" font="Regular;28"/>
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/Enigmawelt/img/head_logo.png" position="1150,5" size="40,40" alphatest="blend" scale="1" />
		<widget source="movielist" render="Listbox" position="10,50" size="700,485" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{
				"templates":
					{
					"default": (40,
						[
						MultiContentEntryText(pos=(5, 0), size=(550, 35), font=0, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=0),
						])
					},
				"itemHeight" : 40,
				"fonts": [parseFont("Regular;20")]
				}
			</convert>
		</widget>
		<widget name="cover" position="730,50" size="460,214" alphatest="blend" conditional="cover" scaleFlags="scaleCenter" transparent="1" />
		<widget source="description" render="Label" position="730,275" size="460,285" conditional="description" font="Regular;18" horizontalAlignment="block" />
		<widget source="key_red" render="Label" position="1095,e-40" size="85,40" backgroundColor="white" font="Verdana;25" foregroundColor="black" halign="center" noWrap="1" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_green" render="Label" position="995,e-40" size="85,40" backgroundColor="white" font="Verdana;25" foregroundColor="black" halign="center" noWrap="1" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_yellow" render="Label" position="390,e-45" size="180,35" backgroundColor="key_yellow" conditional="key_yellow" font="Regular;18" foregroundColor="key_text" halign="center" noWrap="1" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
		<widget source="key_blue" render="Label" position="580,e-45" size="180,35" backgroundColor="key_blue" conditional="key_blue" font="Regular;18" foregroundColor="key_text" halign="center" noWrap="1" valign="center">
			<convert type="ConditionalShowHide" />
		</widget>
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "DirectionActions", "ChannelSelectBaseActions", "MenuActions"],
			{
				"green": self.ok,
				"red": self.exit,
#				"blue": self.Home,
				"up": self.up,
				"down": self.down,
				"left": self.left,
				"right": self.right,
				"nextBouquet": self.p_up,
				"prevBouquet": self.p_down,
				"ok": self.ok,
				"cancel": self.exit
			}, -1)
		self["movielist"] = List()
		self["cover"] = Pixmap()
		self["description"] = StaticText()
		self["key_red"] = StaticText("EXIT")
		self["key_green"] = StaticText("OK")
		self["key_yellow"] = StaticText()
		self["key_blue"] = StaticText()
		self._items = []
		if not exists("/tmp/ewcover/"):
			mkdir("/tmp/ewcover/")
		self.onLayoutFinish.append(self.mainMenu)
		self.setTitle("Enigmawelt | Der größte DreamOS/Enigma2 Video Blog")

	def getUrl(self, data):
		parse = re.search(r"/embed/(.*)\?cover", data, re.S)
		if parse:
			return parse.group(1)
		else:
			return None

	def parseData(self, data):
		self._items = []
		try:
			items = loads(data)
			if 'items' in items:
				for item in items['items']:
					title = item.get('title')
					url = item.get('content_html')
					tags = item.get('tags')
					if tags and "Blog" in tags:
						continue
					if url:
						image_url = item.get('image')
						content_text = item.get('content_text')
						pos = content_text.find("\n\n")
						if pos > 0:
							content_text = content_text[:pos]
						url = self.getUrl((url))
						self._items.append((title, url, image_url, content_text))
		except Exception as e:
			pass

	def mainMenu(self):
		def getList():
			data = geturl("https://enigmawelt.de/feed/json")
			if data:
				self.parseData(data)
				self["movielist"].list = self._items
				self.infos()

		callInThread(getList)

	def ok(self):
		url = self["movielist"].getCurrent()[1]
		url = "https://public-api.wordpress.com/rest/v1.1/videos/%s" % url
		data = geturl(url)
		try:
			js = loads(data)
			videourl = js["original"]
			self.Play(videourl, self["movielist"].getCurrent()[0])
		except Exception as e:
			print(e)
			pass

	def exit(self):
		self.close()

	def Play(self, url, title):
		if url:
			sref = eServiceReference(4097, 0, url)
			sref.setName(title)
			self.session.open(MoviePlayer2, sref)

	def up(self):
		if self["movielist"]:
			self["movielist"].up()
			self.infos()

	def down(self):
		if self["movielist"]:
			self["movielist"].down()
			self.infos()

	def left(self):
		if self["movielist"]:
			self["movielist"].pageUp()
			self.infos()

	def right(self):
		if self["movielist"]:
			self["movielist"].pageDown()
			self.infos()

	def p_up(self):
		pass
#		self["handlung"].pageUp()

	def p_down(self):
		pass
#		self["handlung"].pageDown()

	def infos(self):
		description = self["movielist"].getCurrent()[3]
		self["description"].setText(description)
		self.show_cover()

	def show_cover(self):
		if self["movielist"].getCurrent() is not None:
			url = self["movielist"].getCurrent()[2]
			if url.startswith("http"):
				callInThread(self.getimage, url)
			elif url.startswith("/usr/"):
				self.get_cover(url)
			else:
				img = PLUGINPATH + "/img/nocover.png"
				self.get_cover(img)

	def getimage(self, url):
		try:
			imgpath = join(TMPIC, base64.b64encode(url.split("/")[-1].encode("ascii")).decode("ascii") + ".jpg")
			if not exists(imgpath):
				width = str(self["cover"].instance.size().width())
				url = url.replace("?fit=1500", "?fit=" + width)
				print("getimage", url)

				data = geturl(url)

				with open(imgpath, "wb") as f:
					f.write(data)

#			img = Image.open(TMPIC)
#			img = img.convert('RGB', colors=256)
#			aspect = (200 / float(img.size[0]))
#			height = int((float(img.size[1]) * float(aspect)))
#			img = img.resize((200, height), Image.LANCZOS)
#			img.save(TMPIC)
			self.get_cover(imgpath)
		except OSError as e:
			print("OSError", e)
#			pass

	def get_cover(self, img):
		picload = ePicLoad()
		self["cover"].instance.setPixmap(gPixmapPtr())
		size = self["cover"].instance.size()
		picload.setPara((size.width(), size.height(), 1, 1, False, 1, "#FF000000"))
		if picload.startDecode(img, 0, 0, False) == 0:
			ptr = picload.getData()
			if ptr is not None:
				self["cover"].instance.setPixmap(ptr)
				self["cover"].show()


class MoviePlayer2(MoviePlayer):

	def __init__(self, session, service):
		MoviePlayer.__init__(self, session, service)
		self.skinName = "MoviePlayer"

	def up(self):
		pass

	def down(self):
		pass

	def leavePlayer(self):
		self.close()

	def leavePlayerOnExit(self):
		self.leavePlayer()

	def doEofInternal(self, playing):
		if not playing or not self.execing:
			return
		self.close()


def main(session, **kwargs):
	session.open(enimaWeltScreen)


def Plugins(**kwargs):
	return PluginDescriptor(name="Enigmawelt", description="Der größte DreamOS/Enigma2 Video Blog", where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=main)
