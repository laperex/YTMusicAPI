from hashlib import sha1
import time
import requests


class YTMusicAPI:
	def __init__(self, __Secure_3PSID: str, __Secure_3PAPISID: str, x_origin: str, user_agent: str, key: str="AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30"):
		self.__Secure_3PSID = __Secure_3PSID
		self.__Secure_3PAPISID = __Secure_3PAPISID
		self.x_origin = x_origin
		self.user_agent = user_agent
		self.key = key
		self.payload = {
			"context": {
				"client": {
					"clientName": "WEB_REMIX",
					"clientVersion": "1.20210920.01.00"
				}
			}
		}

	def __init__(self):
		self.__Secure_3PSID = "EQjEgbjJXe5lPzGU3qRIgLB9vrfqKXawkKnXUlRPw5_sDYGI6nhgtVBO4DEkYtu1Nm9k3A."
		self.__Secure_3PAPISID = "bdp7OSsczp8HquJp/ARkKlf3fznr3VYPUc"
		self.x_origin = 'https://music.youtube.com'
		self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0'
		self.key = "AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30"
		self.payload = {
			"context": {
				"client": {
					"clientName": "WEB_REMIX",
					"clientVersion": "1.20210920.01.00"
				}
			}
		}

	def google_auth(self):
		sha_1 = sha1()
		unix_timestamp = str(int(time.time()))
		sha_1.update((unix_timestamp + ' ' + (self.__Secure_3PAPISID + ' ' + "https://music.youtube.com")).encode('utf-8'))
		return "SAPISIDHASH " + unix_timestamp + "_" + sha_1.hexdigest()

	def __request(self, url: str, referer: str="", data:dict={}):
		
		self.payload.update(data)

		return requests.post("https://music.youtube.com/youtubei/v1/" + url + "&key=" + self.key, headers={
			'x-origin': self.x_origin,
			'authorization': self.google_auth(),
			'user-agent': self.user_agent,
			'referer': 'https://music.youtube.com/' + referer,
			'cookie': '__Secure-3PSID=' + self.__Secure_3PSID + '; __Secure-3PAPISID=' + self.__Secure_3PAPISID,
			
		}, data=str(self.payload))

	def get_playlist_songs(self, id: str):
		res = self.__request("browse?", "playlist?list=" + id, {"browseId": "VL" + id}).json()

		path = res['contents']['singleColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['musicPlaylistShelfRenderer']['contents']
		idx = 0
		while 'contents' in res or 'continuationContents' in res:
			for i in range(len(path)):
				idx += 1
				try:
					yield (idx, path[i]['musicResponsiveListItemRenderer']['playlistItemData']['videoId'])
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

	def clone_playlist(self, initial_playlist: str, target_playlist: str):
		target = self.get_playlist_songs(target_playlist)

		for song in self.get_playlist_songs(initial_playlist):
			if song not in target:
				self.add_song_to_playlist(song, target_playlist)
	
	def create_playlist(self, name: str, description: str="", privacy: int=3):	# Private - 3 | Unlisted - 2 | Public - 1
		print(self.__request("playlist/create?", data={"title": name, "description": description, "privacyStatus": privacy}))
	
	def get_music_data(self, song_id):
		return self.__request("player?", data={"videoId": song_id}).json()['videoDetails']
