#!/bin/python3
# A script for extracting Puzzle & Character examples from clockchecker and
# populating the webapp.

from os.path import dirname, join, realpath
import re
from shutil import copyfile
import subprocess


root_dir = realpath(join(dirname(__file__), '..'))
puzzles_file = join(root_dir, 'puzzles.py')
puzlesjs_file = join(root_dir, 'webapp', 'puzzles.js')
blog_file = join(root_dir, 'webapp', 'NQT_blogspot.html')  # TODO: wget the latest page each time
nqt_page = "https://notquitetangible.blogspot.com/2024/11/clocktower-puzzle-archive.html"

puzzle_pattern = re.compile(r'\ndef _?puzzle_(.*)\(\):\n([\s\S]*?\n)    solutions =')
claim_pattern = re.compile(r"Player\('.*?', claim=(.+?)[,)]")
hidden_pattern = re.compile(r"hidden_characters=\[(\w*(?:,\s*\w+)*)\s*\]")
preamble_pattern = re.compile(r"Player\('.*?', claim=(.+?)[,)]")
nqt_metadata_pattern = re.compile(
r'''<tr>
    <td style="text-align: center;"><span style="font-family: helvetica;">([0-9a-z]+?)</span></td>
    <td>(?:<span style="font-family: helvetica;">)?<a href="(.*?)">(?:<span style="font-family: helvetica;">)?(.+?)(?:</span>)?</a>( \(.+?\))?(?:</span>)?</td>
    <td><span style="font-family: helvetica;">(.*?)</span></td>
    <td><span style="font-family: helvetica;">(.*?)</span></td>
    <td>(?:<span style="font-family: helvetica;">)?(.*?)(?:</span>)?</td>'''
)

entry_template = """{{
name: '{name}',
claims: {claims},
hidden: {hidden},
value:\n`{preamble}{puzzle}`
}}"""

puzzles_js_template = """
// This file was auto-generated using clockchecker/webapp/update_content.py
const puzzleSamples = {{
    "NotQuiteTangible": [{nqt_entries}\n], "Other": [{other_entries}\n],
}};
"""

def mv(fname):
	copyfile(
		src=join(root_dir, 'clockchecker', f'{fname}.py'),
		dst=join(root_dir, 'webapp', 'clockchecker', fname),
	)

def get_nqt_metadata(blog_content):
	matches = nqt_metadata_pattern.findall(blog_content)
	output = {}
	for number, url, title, title2, claims, hidden, note in matches:
		output[f'NQT{number}'] = {
			'url': url,
			'title': title + title2,
			'claims': claims.split(', '),
			'hidden': hidden.split(', '),
			'note': note,
		}

	output['NQT30a'] = output['NQT30']
	output['NQT30b'] = output['NQT30']
	return output

def parse_body(body):
	claims = claim_pattern.findall(body)
	hidden = [x.strip() for x in hidden_pattern.search(body).group(1).split(',')]

	lines = (l[4:] for l in body.splitlines())
	preamble = []
	for line in lines:
		line_content = line.strip()
		if line_content and not line_content.startswith('#'):
			puzzle = '\n'.join([line] + list(lines))
			break
		preamble.append(line)
	else:
		raise ValueError(
			f'Failed to find preamble in puzzle starting with \n"{lines[0]}"\n'
		)
	preamble = '\n'.join(preamble)
	return claims, hidden, preamble, puzzle


if __name__ == '__main__':

	result = subprocess.run(
		["wget", nqt_page, "-O", blog_file],
		stderr=subprocess.STDOUT,
		check=True,
	)
	with open(blog_file, 'r') as f:
		nqt_metadata = get_nqt_metadata(f.read())

	with open(puzzles_file, 'r') as f:
		puzzles = puzzle_pattern.findall(f.read())

	nqt_entries, other_entries = [], []

	for name, body in puzzles:
		claims, hidden, preamble, puzzle = parse_body(body)

		if name in nqt_metadata:
			meta = nqt_metadata[name]
			preamble = f'# {name}: {meta['title']}\n# {meta['url']}\n'
			if meta['note']:
				preamble += f'# Notes: {meta['note']}\n'
		else:
			preamble = f'# Other: {name}\n{preamble}\n'		

		entry =	entry_template.format(
			name=name,
			claims=claims,
			hidden=hidden,
			preamble=preamble,
			puzzle=puzzle,
		)
		(nqt_entries if name.startswith('NQT') else other_entries).append(entry)

	with open(puzlesjs_file, 'w') as f:
		f.write(puzzles_js_template.format(
			nqt_entries=', '.join(nqt_entries),
			other_entries=', '.join(other_entries),
		))

	mv('__init__')
	mv('core')
	mv('characters')
	mv('events')
	mv('info')

	print(f'Update Complete: {len(puzzles)} puzzles')



## ------------- TMP ------------ ##


characters_js_template = '''
const characterSamples = {{
    "Townsfolk": [\n        {entries}
    ],
    "Outsiders": [
    ],
    "Minions": [
    ],
    "Demons": [
    ],
    "Homebrews": [
    ],
};
'''

def extract_characters():
	p1 = re.compile(r"( {12}Player\('.*?', claim=([^,)]+?)\))")
	p2 = re.compile(r"( {12}Player\('.*?', claim=([^,)]+?),[\s\S]\n+? {12}}?\))")
	with open(puzzles_file, 'r') as f:
		text = f.read()
		players = p1.findall(text) + p2.findall(text)
	all_characters = {}
	for player, claim in players:
		player_lines = [ln[12:] for ln in player.splitlines()]
		if len(player_lines) > len(all_characters.get(claim, [])):
			all_characters[claim] = player_lines

	entries = sorted(all_characters.items())
	entries = [f'{{ name: "{nm}", value: {repr('\n'.join(val) + ',\n')}}}' for nm, val in entries]
	characters_js = characters_js_template.format(entries=',\n        '.join(entries))
	# with open('characters.js', 'w') as f:
		# f.write(characters_js)

# if __name__ == '__main__':
# 	extract_characters()
