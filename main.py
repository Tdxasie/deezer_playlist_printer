import json
import re
import requests
import os.path
import shutil
from fpdf import FPDF
import argparse

pdf_w=210
pdf_h=297

def download_data(playlist_id):
	url = f"https://api.deezer.com/playlist/{playlist_id}"
	data = requests.get(url).content
	with open("data.json", "wb") as writer:
			writer.write(data)


def read_loved_tracks():
	with open("data.json", "r") as loved_tracks:
		data = json.load(loved_tracks)
	tracks = data["tracks"]["data"]
	print(f"Found {len(tracks)} tracks")
	return tracks


def isolate_info(tracks):
	names_and_artists = []
	for track in tracks:
		info = {}
		info["title"] = re.sub("([\(\[]).*?([\)\]])", "", track["title_short"])
		info["title"] = (info["title"][:26] + '..') if len(info["title"]) > 26 else info["title"]
		info["artist"] = track["artist"]["name"]

		# download image
		name = "".join(x for x in info['title'] if x.isalnum())
		path = f"imgs/{name}.jpg"
		if not os.path.isfile(path):
			url = track["album"]["cover_small"]
			if url is not None: 
				img_data = requests.get(url).content
				with open(path, "wb") as writer:
					writer.write(img_data)
				print(f"Downloaded image for {info['title']}")
			else: # Use placeholder if missing thumbnail
				shutil.copy("placeholder.jpg", path)
				print(f"Used placeholder for {name}")

		info["img_path"] = path
		names_and_artists.append(info)
	print(f"Got {len(names_and_artists)} Infos")
	return names_and_artists

class PDF(FPDF):
	def create_track(self, info):
		self.previous_corner = (self.get_x(), self.get_y())
		self.image(info["img_path"])
		self.next_corner = (self.get_x(), self.get_y())
		self.set_xy(self.previous_corner[0] + 20, self.previous_corner[1] + 5)
		self.set_font('FreeMono', 'B', 14)
		self.cell(w=86, ln=2, txt=info["title"])
		self.set_xy(self.previous_corner[0] + 20, self.previous_corner[1] + 15)
		self.set_font('FreeMono', '', 14)
		self.cell(w=86, ln=2, txt=info["artist"])
	
	def generate_tracks(self, infos):
		self.add_page()
		self.set_xy(0, 0)
		for i, info in enumerate(infos):
			self.create_track(info)
			if i%13 == 0 and i != 0:
				x, y = self.next_corner
				self.next_corner = x + pdf_w/2, 0 
			if i%26 == 0 and i != 0:
				self.add_page()
				self.next_corner = 0, 0
			self.set_xy(*self.next_corner)
			

def create_pdf(infos):
	# 12 tracks per page
	pdf = PDF()
	pdf.add_font('FreeMono', '', 'font/FreeMono.ttf', uni=True)
	pdf.add_font('FreeMono', 'B', 'font/FreeMonoBold.ttf', uni=True)
	pdf.generate_tracks(infos)
	pdf.output("final.pdf", "F")

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-i", "--playlist_id", type=int, help="Deezer playlist id", required=True)
	args = parser.parse_args()

	# download data
	download_data(args.playlist_id)
	# lire les loved tracks
	tracks = read_loved_tracks()
	# isoler le nom (short title) et l'artiste & miniatures
	infos = isolate_info(tracks)
	# créer le pdf 
	create_pdf(infos)
	

if __name__ == "__main__":
	main()
