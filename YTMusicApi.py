from hashlib import sha1
import time
import requests
import sqlite3

# Tested on Mozilla FireFox

class YTMusicAPI:
	def __init__(self, profile_path: str=""):
		self.__Secure_3PSID = ""
		self.__Secure_3PAPISID = ""

		if profile_path:
			conn = sqlite3.connect(profile_path)
			c = conn.cursor()

			for row in c.execute('SELECT * FROM moz_cookies;'):
				if row[4] == '.youtube.com' and row[2] == '__Secure-3PAPISID':
					self.__Secure_3PAPISID = row[3]
				if row[4] == '.youtube.com' and row[2] == '__Secure-3PSID':
					self.__Secure_3PSID = row[3]
			
			c.close()
			conn.close()
		
		self.authentication = self.google_auth()
		self.payload = {
			"context": {
				"client": {
					"clientName": "WEB_REMIX",
					"clientVersion": "1.20210920.01.00"
				}
			}
		}

	def google_auth(self):
		if not self.__Secure_3PAPISID:
			return ""
		sha_1 = sha1()
		unix_timestamp = str(int(time.time()))
		sha_1.update((unix_timestamp + ' ' + (self.__Secure_3PAPISID + ' ' + "https://music.youtube.com")).encode('utf-8'))
		return "SAPISIDHASH " + unix_timestamp + "_" + sha_1.hexdigest()

	def __request(self, url: str, referer: str="", data:dict={}):		
		if data:
			self.payload.update(data)

		return requests.post("https://music.youtube.com/youtubei/v1/" + url + "&key=AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30", headers={
			'x-origin': "https://music.youtube.com",
			'authorization': self.authentication,
			'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0",
			'referer': 'https://music.youtube.com/' + referer,
			'cookie': '__Secure-3PSID=' + self.__Secure_3PSID + '; __Secure-3PAPISID=' + self.__Secure_3PAPISID,
			
		}, data=str(self.payload))

	def get_playlist_songs(self, id: str):
		res = self.__request("browse?", "playlist?list=" + id, {"browseId": "VL" + id}).json()

		path = res['contents']['singleColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['musicPlaylistShelfRenderer']['contents']
		
		while 'contents' in res or 'continuationContents' in res:
			for i in range(len(path)):
				try:
					yield path[i]['musicResponsiveListItemRenderer']['playlistItemData']['videoId']
				except KeyError:
					continue

			if 'contents' in res:
				if 'continuations' in res['contents']['singleColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['musicPlaylistShelfRenderer']:
					itct = res['contents']['singleColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['musicPlaylistShelfRenderer']['continuations'][0]['nextContinuationData']['clickTrackingParams']
					ctoken = res['contents']['singleColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['musicPlaylistShelfRenderer']['continuations'][0]['nextContinuationData']['continuation']
				else:
					break
			else:
				if 'continuations' in res['continuationContents']['musicPlaylistShelfContinuation']:
					itct = res['continuationContents']['musicPlaylistShelfContinuation']['continuations'][0]['nextContinuationData']['clickTrackingParams']
					ctoken = res['continuationContents']['musicPlaylistShelfContinuation']['continuations'][0]['nextContinuationData']['continuation']
				else:
					break


			res = self.__request("browse?type=next" + "&ctoken=" + ctoken + "&continuation=" + ctoken + "&itct=" + itct, "playlist?list=" + id, {"browseId": "VL" + id}).json()
			path = res['continuationContents']['musicPlaylistShelfContinuation']['contents']

	def add_song_to_playlist(self, song_id: str, playlist_id: str):
		return self.__request("browse/edit_playlist?", "playlist?list=" + playlist_id, {"actions": [
			{
				"addedVideoId": song_id,
				"action": "ACTION_ADD_VIDEO",
				"dedupeOption": "DEDUPE_OPTION_CHECK"
			}
		], "playlistId": playlist_id})

	def copy_playlist(self, initial_playlist: str, target_playlist: str):
		target = [i for i in self.get_playlist_songs(target_playlist)]

		for song in self.get_playlist_songs(initial_playlist):
			if song not in target:
				self.add_song_to_playlist(song, target_playlist)
	
	def create_playlist(self, name: str, description: str="", privacy: int=3):	# Private - 3 | Unlisted - 2 | Public - 1
		print(self.__request("playlist/create?", data={"title": name, "description": description, "privacyStatus": privacy}))

	# No Sign In Required
	
	def get_music_data(self, song_id):
		return self.__request("player?", data={"videoId": song_id}).json()['videoDetails']

	def search_song(self, query: str):
		return self.__request(query)
