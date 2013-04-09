#!/usr/bin/env python2
import sys
import MumbleConnection
import IRCConnection
import ConsoleConnection
import time
import ConfigParser
import os.path
import re
import urllib

irc = None
mumble = None
console = None

conffile = "sftbot.conf"

def mumbleTextMessageCallback(sender, message):
	line="mumble: " + sender + ": " + message
	console.sendTextMessage(line)
	irc.sendTextMessage(line)
	if(message == 'gtfo'):
		mumble.sendTextMessage("KAY CU")
		mumble.stop()

def ircTextMessageCallback(sender, message):
	line="irc: " + sender + ": " + message
	console.sendTextMessage(line)
	mumble.sendTextMessage(line)
	if (message == 'gtfo'):
		irc.sendTextMessage("KAY CU")
		irc.stop()

def consoleTextMessageCallback(sender, message):
	line="console: " + message
	irc.sendTextMessage(line)
	mumble.sendTextMessage(line)

def mumbleDisconnected():
	line="connection to mumble lost. reconnect in 5 seconds."
	console.sendTextMessage(line)
	irc.sendTextMessage(line)
	time.sleep(5)
	mumble.start()

def mumbleConnectionFailed():
	line="connection to mumble failed. retrying in 15 seconds."
	console.sendTextMessage(line)
	irc.sendTextMessage(line)
	time.sleep(15)
	mumble.start()

def ircDisconnected():
	line="connection to irc lost. reconnect in 15 seconds."
	console.sendTextMessage(line)
	mumble.sendTextMessage(line)
	time.sleep(15)
	irc.start()

def ircConnectionFailed():
	line="connection to irc failed. retrying in 15 seconds."
	console.sendTextMessage(line)
	mumble.sendTextMessage(line)
	time.sleep(15)
	irc.start()

def resolveUrls(sender, message):
	# because fuck you and your code style guidelines, that's why!
	baddern = re.compile("^((([hH][tT][tT][pP][sS]?|[fF][tT][pP])\:\/\/)?([\w\.\-]+(\:[\w\.\&%\$\-]+)*@)?((([^\s\(\)\<\>\\\"\.\[\]\,@;:]+)(\.[^\s\(\)\<\>\\\"\.\[\]\,@;:]+)*(\.[a-zA-Z]{2,4}))|((([01]?\d{1,2}|2[0-4]\d|25[0-5])\.){3}([01]?\d{1,2}|2[0-4]\d|25[0-5])))(\b\:(6553[0-5]|655[0-2]\d|65[0-4]\d{2}|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0)\b)?((\/[^\/][\w\.\,\?\'\\\/\+&%\$#\=~_\-@]*)*[^\.\,\?\"\'\(\)\[\]!;<>{}\s\x7F-\xFF])?)$")
	result = baddern.match(message)
	if result:
		# open the url in urllib to get it's title
		try:
			html = urllib.urlopen(result.group(0))
			title = html.read().split('<title>')[1].split('</title>')[0].strip()
			line = "page title = {0}".format(title)

		except IOError:
			line = "failed to connect to webserver"

		#send line to the connections
		console.sendTextMessage(line)
		mumble.sendTextMessage(line)
		irc.sendTextMessage(line)


def main():
	global mumble
	global irc
	global console

	loglevel = 3

	if not os.path.isfile(conffile):
		raise Exception('configuration file {0} not found or unreadable. fix pls.'.format(conffile))

	#create python's configparser and read our configfile
	cparser = ConfigParser.ConfigParser()
	cparser.read(conffile)

	#configuration for the mumble connection
	mblservername = cparser.get('mumble', 'server')
	mblport = int(cparser.get('mumble', 'port'))
	mblnick = cparser.get('mumble', 'nickname')
	mblchannel = cparser.get('mumble', 'channel')
	mblpassword = cparser.get('mumble', 'password')
	mblloglevel = int(cparser.get('mumble', 'loglevel'))

	#configuration for the IRC connection
	ircservername = cparser.get('irc', 'server')
	ircport = int(cparser.get('irc', 'port'))
	ircnick = cparser.get('irc', 'nickname')
	ircchannel = cparser.get('irc', 'channel')
	ircencoding = cparser.get('irc', 'encoding')
	ircloglevel = int(cparser.get('irc', 'loglevel'))


	# create server connections
	#hostname, port, nickname, channel, password, name, loglevel
	mumble = MumbleConnection.MumbleConnection(mblservername, mblport, mblnick, mblchannel, mblpassword, "mumble", mblloglevel)
	irc = IRCConnection.IRCConnection(ircservername, ircport, ircnick, ircchannel, ircencoding, "irc", ircloglevel)
	console = ConsoleConnection.ConsoleConnection("utf-8", "console", loglevel)

	# register text callback functions
	mumble.registerTextCallback(resolveUrls)
	irc.registerTextCallback(resolveUrls)
	mumble.registerTextCallback(mumbleTextMessageCallback)
	irc.registerTextCallback(ircTextMessageCallback)
	console.registerTextCallback(consoleTextMessageCallback)

	# register connection-lost callback functions
	irc.registerConnectionLostCallback(ircDisconnected)
	mumble.registerConnectionLostCallback(mumbleDisconnected)

	# register connection-failed callback functions
	irc.registerConnectionFailedCallback(ircConnectionFailed)
	mumble.registerConnectionFailedCallback(mumbleConnectionFailed)

	# start the connections. they will be self-sustaining due to the callback functions
	mumble.start()
	irc.start()

	#use the console as main loop
	console.run()

if __name__=="__main__":
	main()
