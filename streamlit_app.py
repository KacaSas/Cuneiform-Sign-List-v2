import csv
import pandas as pd
import re
import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, JsCode
import streamlit.components.v1 as components
import base64  # load cuneiform fonts
import unicodedata  # custom alphabetical sort
import warnings

#from PIL import Image, ImageOps
#import json
#import ijson

st.set_page_config(page_title='Cuneiform sign list 2', page_icon='resources/icon/icon.png', layout='wide')  # change favicon and page title

# load cuneiform fonts
def load_font_css(font_name, font_path):
	with open(font_path, "rb") as f:
		font_data = f.read()
		b64_font = base64.b64encode(font_data).decode()
		return f"""
		@font-face {{
			font-family: '{font_name}';
			src: url(data:font/ttf;base64,{b64_font}) format('truetype');
		}}
		"""
fonts_css = ""
fonts_css += load_font_css("PCSL", "resources/fonts/PCSL.ttf")
fonts_css += load_font_css("Sinacherib", "resources/fonts/Sinacherib.ttf")
fonts_css += load_font_css("Santakku", "resources/fonts/Santakku.ttf")
fonts_css += load_font_css("SantakkuM", "resources/fonts/SantakkuM.ttf")
fonts_css += load_font_css("Assurbanipal", "resources/fonts/Assurbanipal.ttf")
fonts_css += load_font_css("OB Freie", "resources/fonts/OBFreie-Regular.ttf")
fonts_css += load_font_css("CuneiformComposite", "resources/fonts/CuneiformComposite.ttf")
fonts_css += load_font_css("Esagil", "resources/fonts/Esagil.ttf")
fonts_css += load_font_css("Nabu-ninua-ihsus", "resources/fonts/Nabuninuaihsus.ttf")
fonts_css += load_font_css("Gudea", "resources/fonts/Oracc-gudea.ttf")
fonts_css += load_font_css("Oracc LAK", "resources/fonts/Oracc-LAK.ttf")
fonts_css += load_font_css("Oracc RSP", "resources/fonts/Oracc-RSP.ttf")

st.markdown(f"<style>{fonts_css}</style>", unsafe_allow_html=True)  # insert fonts into the app page

def clearSignListForm():
	st.session_state['searchSign'] = ''
	st.session_state['searchMesZL'] = ''
	st.session_state['searchABZ'] = ''
	st.session_state['searchCodepoint'] = ''

def customAlphabetSort(sortedDF, sortedColumn):
	customAlphabet = list(' .–-0₀1₁2₂3₃4₄5₅6₆7₇8₈9₉ʾ’ʿ‘`AaĀāÂâÁáÀàÄäBbCcÇçDdḌḍḎḏEeĒēÉéÊêÈèËëFfGgĞğǦǧHhḪḫḤḥIiĪīÎîÍíÌìİıÏïJjKkLlMmNnOoŌōÔôÓóÖöPpQqRrŘřSsṢṣŞşŠšTtṬṭŢţṮṯUuŪūÛûÚúÙùÜüVvWwXxYyZz!"#$%_()*+,/:;<=>?@[]^&{|}~')
	lowercaseAlphabet = [char.lower() for char in customAlphabet]
	charOrder = {char: i for i, char in enumerate(lowercaseAlphabet)}
	baseVowels = {'a', 'e', 'i', 'o', 'u', 'A', 'E', 'I', 'O', 'U'}
	def normalizeText(text):
		normalized = []
		for char in str(text):
			lowerChar = char.lower()
			decomposed = unicodedata.normalize('NFKD', lowerChar)
			baseChar = decomposed[0] if len(decomposed) > 0 else lowerChar
			if baseChar in baseVowels:
				normalized.append(baseChar)
			else:
				normalized.append(lowerChar)
		return ''.join(normalized)
	def sortKey(word):
		normalized = normalizeText(word)
		return [charOrder.get(char, len(customAlphabet)) for char in normalized]
	sortedDF = sortedDF.sort_values(by=sortedColumn, key=lambda x: x.map(sortKey))
	return sortedDF

st.write('<b><font style="font-size: 36px">Cuneiform signs search</font></b><br>(case insensitive, regular expressions allowed)', unsafe_allow_html=True)
st.write('<font style="font-size: 1.1em; color: #2e9aff">Cuneiform fonts used in this app are available thanks to the efforts of S. Vanséveren, S. Tinney, C. R. Ziegeler, R. Leroy, and others. Individual cuneiform signs are mapped according to my <a href="http://home.zcu.cz/~ksaskova/Sign_List.html" target="_blank"><i>Cuneiform Sign List</i></a>; the mapping of Proto-Cuneiform signs follows the <a href="https://oracc.museum.upenn.edu/pcsl/" target="_blank"><i>Proto-Cuneiform Sign List</i></a>. Sumerian and Akkadian glossaries are taken from <a href="https://oracc.museum.upenn.edu/epsd2/" target="_blank"><i>ePSD2: The Pennsylvania Sumerian Dictionary Project</i></a> and <a href="https://oracc.museum.upenn.edu/tsae/" target="_blank"><i>TSAE: Textual Sources of the Assyrian Empire</i></a>. For details, see <i>Sources and references</i> below.</font><br><br>', unsafe_allow_html=True)

#st.divider()

######################################## SIGN SEARCH ########################################
colu1, colu2, colu3, colu4, colu5 = st.columns([1, 2, 1, 1, 1])
with colu1:
	searchShape = st.selectbox('Initial wedge shape:', ('𒀸 AŠ', '𒋰 TAB', '𒀼 EŠ16', '𒀹 GE23', '𒌋 U', '𒁹 DIŠ'), index=None, placeholder='Initial wedge shape', key='searchShape', label_visibility='collapsed')
with colu2:
	searchSign = st.text_input('Name/Value:', placeholder='Name/Value', key='searchSign', label_visibility='collapsed')
with colu3:
	searchMesZL = st.text_input('MesZL number:', placeholder='MesZL number', key='searchMesZL', label_visibility='collapsed')
with colu4:
	searchABZ = st.text_input('ABZ/Labat number:', placeholder='ABZ/Labat number', key='searchABZ', label_visibility='collapsed')
with colu5:
	searchCodepoint = st.text_input('Unicode codepoint:', placeholder='Unicode codepoint', key='searchCodepoint', label_visibility='collapsed')
	
co1, co2 = st.columns([5.015, 0.985])
with co1:
	onlyWholeWordSearch = st.checkbox('Search whole string only (name/value)', key='onlyWholeWordSearch', value=False)
with co2:
	clearSignListForm = st.button('Clear form', key='clearSignListForm', on_click=clearSignListForm, use_container_width=True)  # clear form

data = pd.read_csv('resources/signList/SignList.csv', keep_default_na=False, na_values=[])

if searchSign != '':
	searchSignOrigin = searchSign  # keep original search term
	replacementsSearchSign = {'Sh': 'Š', 'sh': 'š', 'kh': 'ḫ', 'H': 'Ḫ', 'h': 'ḫ', r',s': r'\,s', r'\,s': r'ṣ', r',S': r'\,S', r'\,S': r'Ṣ', r',t': r'\,t', r'\,t': r'ṭ', r',T': r'\,T', r'\,T': r'Ṭ', r'.': r'\.'}
	for old, new in replacementsSearchSign.items():
		searchSign = searchSign.replace(old, new)
	searchSign = searchSign.replace('+', '\\+')
	searchSignWithoutRegExp = searchSign
	if onlyWholeWordSearch:
		searchSign = r'(?<!\w)' + searchSign + r'(?!\w)'

	foundSign1 = data.loc[data['Name'].str.contains(searchSign, case=False, regex=True)]
	foundSign2 = data.loc[data['Values'].str.contains(searchSign, case=False, regex=True)]
	foundSign3 = data.loc[data['Sign'].str.contains(searchSign, case=False, regex=True)]
	foundSign4 = data.loc[data['Values3'].str.contains(searchSign, case=False, regex=True)]
	foundSign5 = data.loc[data['Values2'].str.contains(searchSign, case=False, regex=True)]
	foundSign = pd.concat([foundSign1, foundSign2, foundSign3, foundSign4, foundSign5], axis=0, join='outer', ignore_index=False, keys=None)
	foundSign = foundSign.drop_duplicates(inplace=False)
else:
	foundSign = data

if searchMesZL != '':
	foundMesZL = foundSign.loc[data['MesZL'].str.contains(searchMesZL, case=False, regex=True)]
else:
	foundMesZL = foundSign

if searchABZ != '':
	foundABZ = foundMesZL.loc[data['ABZ/Labat'].str.contains(searchABZ, case=False, regex=True)]
else:
	foundABZ = foundMesZL

if searchShape != '':
	if searchShape == '𒀸 AŠ':
		foundShape = foundABZ[foundABZ['MesZL_nu'].between(1, 208)].sort_values(by=['MesZL'])
	elif searchShape == '𒋰 TAB':
		foundShape = foundABZ[foundABZ['MesZL_nu'].between(209, 504)].sort_values(by=['MesZL'])
	elif searchShape == '𒀼 EŠ16':
		foundShape = foundABZ[foundABZ['MesZL_nu'].between(505, 574)].sort_values(by=['MesZL'])
	elif searchShape == '𒀹 GE23':
		foundShape = foundABZ[foundABZ['MesZL_nu'].between(575, 660)].sort_values(by=['MesZL'])
	elif searchShape == '𒌋 U':
		foundShape = foundABZ[foundABZ['MesZL_nu'].between(661, 747)].sort_values(by=['MesZL'])
	elif searchShape == '𒁹 DIŠ':
		foundShape = foundABZ[foundABZ['MesZL_nu'].between(748, 907)].sort_values(by=['MesZL'])
	else:
		foundShape = foundABZ
else:
	foundShape = foundABZ

if searchCodepoint != '':
	searchCodepoint = searchCodepoint.replace('+', '\\+')
	searchCodepoint = searchCodepoint.replace('(', '\\(')
	searchCodepoint = searchCodepoint.replace(')', '\\)')
	searchCodepoint = searchCodepoint.replace('.', '\\.')
	foundCodepoint = foundShape.loc[data['Codepoint'].str.contains(searchCodepoint, case=False, regex=True)]
else:
	foundCodepoint = foundShape

######################################## SHOW SEARCH RESULT ########################################
foundData = customAlphabetSort(foundCodepoint, 'Name')

cellsytle_jscode = JsCode(
	"""
function(params) {
	if (params.value != '–') {
		return {
			'color': 'white',
			'backgroundColor': '#0E1117',
			'font-size':'15px',
		}
	} else {
		return {
			'color': 'white',
			'backgroundColor': '#262730',
			'font-size':'15px',
		}
	}
};
"""
)

gb = GridOptionsBuilder.from_dataframe(data)
gb.configure_side_bar()
gb.configure_default_column(
	editable=False,
	resizable=True,
	sorteable=True, 
	autoHeight=False,
	headerComponentParams={
		"template":
			'<div class="ag-cell-label-container" role="presentation">' +
			'  <span ref="eMenu" class="ag-header-icon ag-header-cell-menu-button"></span>' +
			'  <div ref="eLabel" class="ag-header-cell-label" role="presentation">' +
			'    <span ref="eSortOrder" class="ag-header-icon ag-sort-order"></span>' +
			'    <span ref="eSortAsc" class="ag-header-icon ag-sort-ascending-icon"></span>' +
			'    <span ref="eSortDesc" class="ag-header-icon ag-sort-descending-icon"></span>' +
			'    <span ref="eSortNone" class="ag-header-icon ag-sort-none-icon"></span>' +
			'    <span ref="eText" class="ag-header-cell-text" role="columnheader" style="font-size: 16px; text-align: right; color: gray;"></span>' +
			'    <span ref="eFilter" class="ag-header-icon ag-filter-icon"></span>' +
			'  </div>' +
			'</div>'
	}
)
gb.configure_selection('', use_checkbox=True, groupSelectsChildren='Group checkbox select children')
gb.configure_columns(['Name', 'Values', 'Meaning', 'MesZL', 'Values1', 'ABZ/Labat', 'Codepoint'], cellStyle=cellsytle_jscode)
gb.configure_column('Sign', maxWidth=250, cellStyle={'fontFamily': 'CuneiformComposite', 'color': 'white', 'backgroundColor': '#0E1117', 'font-size':'23px'})
gb.configure_column('Name', maxWidth=210)
gb.configure_column('MesZL', maxWidth=175)
gb.configure_column('ABZ/Labat', maxWidth=175)
gb.configure_column('Codepoint', maxWidth=270)
gb.configure_column('Sign1', hide=True)
gb.configure_column('Values1', hide=True)
gb.configure_column('Values2', hide=True)
gb.configure_column('Values3', hide=True)
gb.configure_column('Path', hide=True)
gb.configure_column('MesZL_nu', hide=True)
gb.configure_column('NamesForCuenify', hide=True)
gb.configure_column('ValuesForCuenify', hide=True)
gb.configure_grid_options(rowHeight=37)  # set row height
gridOptions = gb.build()

with st.container(border=True):
	st.write('Found items count: ', foundData['Sign'].count())
	grid_response = AgGrid(
		foundData,
		allow_unsafe_jscode=True,
		gridOptions=gridOptions,
		DataReturnMode='AS_INPUT',
		GridUpdateMode='MODEL_CHANGED',
		fit_columns_on_grid_load=True,
		theme='streamlit',  # themes: streamlit, light, dark/balham, blue, fresh, material
		enable_enterprise_modules=False,
		height=190, 
		width='100%',
		reload_data=False
	)

	data = grid_response['data']
	selected = grid_response['selected_rows'] 
	df1 = pd.DataFrame(selected)

######################################## GLOSSARIES PREPARATION FUNCTIONS ########################################
def simpleSearchString(searchString, searchData, columnName):
	if searchString != '':
		with warnings.catch_warnings():
			warnings.filterwarnings('ignore', category=UserWarning, message="This pattern is interpreted as a regular expression")
			foundData = searchData.loc[searchData[columnName].str.contains(searchString, case=False, regex=True)]
	else:
		foundData = searchData
	return foundData

def clearSumerianForm():
	for k in ['meanSumerian', 'meanBaseForm', 'meanAkkadian', 'meanEnglish']:
		st.session_state[k] = ''

def clearAkkadianForm():
	for Ak in ['akkAkkadian', 'akkEnglish', 'akkWrittenForm']:
		st.session_state[Ak] = ''

def sumerianGlossary():
	st.write('<b><font style="font-size: 1.7em; line-height: 2.9em;">Sumerian glossary</font> <font style="font-size: 1.3em; color: #969799;">(from ePSD2)</b></font>', unsafe_allow_html=True)
	colum1, colum2, colum3, colum4 = st.columns([7, 7, 4, 6], gap='small')

	with colum1:
		meanSumerian = st.text_input('Sumerian', placeholder='Sumerian', key='meanSumerian', label_visibility='collapsed')
	with colum2:
		meanBaseForm = st.text_input('Signs / Written form', placeholder='Signs / Written form', key='meanBaseForm', label_visibility='collapsed')
	with colum3:
		meanAkkadian = st.text_input('Akkadian', placeholder='Akkadian', key='meanAkkadian', label_visibility='collapsed')
	with colum4:
		meanEnglish = st.text_input('English', placeholder='English', key='meanEnglish', label_visibility='collapsed')

	columa1, columa2, columa3, columa4 = st.columns([5, 12.9, 0.1, 6], gap='small')
	with columa1:
		st.write('<b><font style="font-size: 1em; color: #969799;">Special characters</b><br> (copy & paste)', unsafe_allow_html=True)
	with columa2:
		st.write('<b><font style="color: #ffffab;">ḫ&ensp; Ḫ&ensp; ṣ&ensp; Ṣ&ensp; š&ensp; Š&ensp; ṭ&ensp; Ṭ&ensp; ŋ&ensp; Ŋ&ensp; ʾ&ensp; ā&ensp; â&ensp; á&ensp; à&ensp; ē&ensp; ê&ensp; é&ensp; è&ensp; ī&ensp; î&ensp; í&ensp; ì&ensp; ū&ensp; û&ensp; ú&ensp; ù&ensp; Ā&ensp; Ē&ensp; Ī&ensp; Ū&ensp; ₀&ensp; ₁&ensp; ₂&ensp; ₃&ensp; ₄&ensp; ₅&ensp; ₆&ensp; ₇&ensp; ₈&ensp; ₉</b></font>', unsafe_allow_html=True)
	with columa4:
		st.button('Clear form', key='clearSumerianForm', on_click=clearSumerianForm, use_container_width=True)  # clear form

	if meanBaseForm != '':
		replacementsSum = {'1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', '0': '₀', 'Sh': 'Š', 'sh': 'š', 'kh': 'ḫ', 'H': 'Ḫ', 'h': 'ḫ', 'ŋ': 'g', 'Ŋ': 'G', r',s': r'\,s', r'\,s': r'ṣ', r',S': r'\,S', r'\,S': r'Ṣ', r',t': r'\,t', r'\,t': r'ṭ', r',T': r'\,T', r'\,T': r'Ṭ', r'.': r'\.'}
		for x,y in replacementsSum.items():
			meanBaseForm = meanBaseForm.replace(x, y)
	if meanSumerian != '':
		replacementsSum1 = {'Sh': 'Š', 'sh': 'š', 'kh': 'ḫ', 'H': 'Ḫ', 'h': 'ḫ', r',s': r'\,s', r'\,s': r'ṣ', r',S': r'\,S', r'\,S': r'Ṣ', r',t': r'\,t', r'\,t': r'ṭ', r',T': r'\,T', r'\,T': r'Ṭ', r'.': r'\.'}
		for x,y in replacementsSum1.items():
			meanSumerian = meanSumerian.replace(x, y)
	if meanAkkadian != '':
		replacementsSum2 = {'Sh': 'Š', 'sh': 'š', 'kh': 'ḫ', 'H': 'Ḫ', 'h': 'ḫ', r',s': r'\,s', r'\,s': r'ṣ', r',S': r'\,S', r'\,S': r'Ṣ', r',t': r'\,t', r'\,t': r'ṭ', r',T': r'\,T', r'\,T': r'Ṭ', r'.': r'\.'}
		for x,y in replacementsSum2.items():
			meanAkkadian = meanAkkadian.replace(x, y)
							
	ePSD2data = pd.read_csv('resources/dictionary/epsd2-dictionary.csv', keep_default_na=False, na_values=[])

	if meanBaseForm != '' or meanSumerian != '' or meanAkkadian != '' or meanEnglish != '':
		foundBaseForm = simpleSearchString(meanBaseForm, ePSD2data, 'base1')
		foundSumerian = simpleSearchString(meanSumerian, foundBaseForm, 'headword1')
		foundAkkadian = simpleSearchString(meanAkkadian, foundSumerian, 'equiv1')
		foundEnglish = simpleSearchString(meanEnglish, foundAkkadian, 'mng1')
		foundMean = foundEnglish

		if len(foundMean) != 0:
			columas1, columas2, columa3s, columas4 = st.columns([17.6, 0.9, 0.1, 6], gap='small')
			if len(foundMean) == 1:
				with columas1:
					st.write('<b><font style="color:#969799; font-size: 1.1em;">Found ', len(foundMean), ' entry</b> (within ', len(ePSD2data), ')</font><br>', unsafe_allow_html=True)
			else:
				with columas1:
					st.write('<b><font style="color:#969799; font-size: 1.1em;">Found ', len(foundMean), ' entries</b> (within ', len(ePSD2data), ')</font><br>', unsafe_allow_html=True)
			with columas4:
				highlight = st.checkbox('Highlight search terms', value=True)

			if highlight and meanBaseForm != '':
				meanBaseForm = r'(' + meanBaseForm + r')'
				foundMean.loc[:, 'base1'] = foundMean['base1'].apply(lambda x: re.sub(meanBaseForm, r'<span style="color:#05ff50; font-weight: bold">\g<0></span>', x, flags=re.IGNORECASE))
			if highlight and meanSumerian != '':
				meanSumerian = r'(' + meanSumerian + r')'
				foundMean.loc[:, 'headword1'] = foundMean['headword1'].apply(lambda x: re.sub(meanSumerian, r'<span style="color:#ff05ee; font-weight: bold">\g<0></span>', x, flags=re.IGNORECASE))				
			if highlight and meanAkkadian != '':
				meanAkkadian = r'(' + meanAkkadian + r')'
				foundMean.loc[:, 'equiv1'] = foundMean['equiv1'].apply(lambda x: re.sub(meanAkkadian, r'<span style="color:#05e6ff; font-weight: bold">\g<0></span>', x, flags=re.IGNORECASE))
			if highlight and meanEnglish != '':
				meanEnglish = r'(' + meanEnglish + r')'
				foundMean.loc[:, 'mng1'] = foundMean['mng1'].apply(lambda x: re.sub(meanEnglish, r'<span style="color:#ff05ee; font-weight: bold">\g<0></span>', x, flags=re.IGNORECASE))
			st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 3px solid #444;'>", unsafe_allow_html=True)
			st.write('<br>', unsafe_allow_html=True)
			for iS, mng_row in foundMean.iterrows():
				with st.container():
					cm1, cm2, cm3, cm4 = st.columns([7, 7, 4, 6], gap='small')
					with cm1:
						st.write(f'<b><font style="font-size: 1.2em;">{mng_row["headword1"]}</font></b>', unsafe_allow_html=True)
					with cm2:
						st.write(f'<b><font style="font-size: 1.1em;">{mng_row["base1"]}</font></b>', unsafe_allow_html=True)
					with cm3:
						st.write(f'<b><i><font style="font-size: 1.1em; color: #ffffab;">{mng_row["equiv1"]}</font></i></b>', unsafe_allow_html=True)
					with cm4:
						st.write(f'<b><font style="font-size: 1.1em;">{mng_row["mng1"]}</font></b>', unsafe_allow_html=True)
					if iS != foundMean.index[-1]:
						st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 1px solid #444;'>", unsafe_allow_html=True)
		else:
			st.write('<br>', unsafe_allow_html=True)
			st.write('<p style="margin-bottom: 6em;"> </p>', unsafe_allow_html=True)
			st.write('<font style="color: #FF4B4B; font-size: 16px"><b>No entries found!</b></font>', unsafe_allow_html=True)
	else:
		st.write('<br>', unsafe_allow_html=True)
		st.write('<p style="margin-bottom: 6em;"> </p>', unsafe_allow_html=True)
		st.write('<font style="color:#FF4B4B; font-size: 16px"><b>Search fields are empty!</b></font>', unsafe_allow_html=True)

	st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 3px solid #444;'>", unsafe_allow_html=True)
	st.write('<br><font style="color: #969799;">Source file <b><i>gloss-sux.json</i></b> (part of <b><i>epsd2.zip</i></b>). <a href="https://oracc.museum.upenn.edu/epsd2/" target="_blank">ePSD2: The Pennsylvania Sumerian Dictionary Project</a>. Available at https://oracc.museum.upenn.edu/epsd2/JSON/index.html.</font>', unsafe_allow_html=True)

def akkadianGlossary():
	st.write('<b><font style="font-size: 1.7em; line-height: 2.9em;">Akkadian glossary</font> <font style="font-size: 1.3em; color: #969799;">(from TSAE)</b></font>', unsafe_allow_html=True)
	column1, column2, column3 = st.columns([5, 5, 5], gap='small')
	with column1:
		akkAkkadian = st.text_input('Akkadian', placeholder='Akkadian', key='akkAkkadian', label_visibility='collapsed')
	with column2:
		akkWrittenForm = st.text_input('Signs / Written form', placeholder='Signs / Written form', key='akkWrittenForm', label_visibility='collapsed')
	with column3:
		akkEnglish = st.text_input('English', placeholder='English', key='akkEnglish', label_visibility='collapsed')

	columa1, columa2, columa3 = st.columns([2.7, 7.3, 5], gap='small')
	with columa1:
		st.write('<b><font style="font-size: 1em; color: #969799;">Special characters</b><br> (copy & paste)', unsafe_allow_html=True)
	with columa2:
		st.write('<b><font style="color: #ffffab;">ḫ&ensp; Ḫ&ensp; ṣ&ensp; Ṣ&ensp; š&ensp; Š&ensp; ṭ&ensp; Ṭ&ensp; ŋ&ensp; Ŋ&ensp; ʾ&ensp; ā&ensp; â&ensp; á&ensp; à&ensp; ē&ensp; ê&ensp; é&ensp; è&ensp; ī&ensp; î&ensp; í&ensp; ì&ensp; ū&ensp; û&ensp; ú&ensp; ù&ensp; Ā&ensp; Ē&ensp; Ī&ensp; Ū&ensp; ₀&ensp; ₁&ensp; ₂&ensp; ₃&ensp; ₄&ensp; ₅&ensp; ₆&ensp; ₇&ensp; ₈&ensp; ₉</b></font>', unsafe_allow_html=True)
	with columa3:
		st.button('Clear form', key='clearAkkadianForm', on_click=clearAkkadianForm, use_container_width=True)  # clear form

	if akkWrittenForm != '':
		replacementsAkk = {'1': '₁', '2': '₂', '3': '₃', '4': '₄', '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉', '0': '₀', 'Sh': 'Š', 'sh': 'š', 'kh': 'ḫ', 'H': 'Ḫ', 'h': 'ḫ', 'ŋ': 'g', 'Ŋ': 'G', r',s': r'\,s', r'\,s': r'ṣ', r',S': r'\,S', r'\,S': r'Ṣ', r',t': r'\,t', r'\,t': r'ṭ', r',T': r'\,T', r'\,T': r'Ṭ', r'.': r'\.'}
		for x,y in replacementsAkk.items():
			akkWrittenForm = akkWrittenForm.replace(x, y)

	if akkAkkadian != '':
		replacementsAkk1 = {'Sh': 'Š', 'sh': 'š', 'kh': 'ḫ', 'H': 'Ḫ', 'h': 'ḫ', r',s': r'\,s', r'\,s': r'ṣ', r',S': r'\,S', r'\,S': r'Ṣ', r',t': r'\,t', r'\,t': r'ṭ', r',T': r'\,T', r'\,T': r'Ṭ', r'.': r'\.'}
		for x,y in replacementsAkk1.items():
			akkAkkadian = akkAkkadian.replace(x, y)

	TSAEdata = pd.read_csv('resources/dictionary/TSAE.csv', keep_default_na=False, na_values=[])

	if akkWrittenForm != '' or akkAkkadian != '' or akkEnglish != '':
		foundWrittenForm = simpleSearchString(akkWrittenForm, TSAEdata, 'Written forms1')
		foundAkkadian = simpleSearchString(akkAkkadian, foundWrittenForm, 'Term')
		foundEnglish = simpleSearchString(akkEnglish, foundAkkadian, 'Meaning1')
		foundAkk = foundEnglish

		if len(foundAkk) != 0:
			columas1, columas2, columas3 = st.columns([9.9, 0.1, 5], gap='small')
			if len(foundAkk) == 1:
				with columas1:
					st.write('<b><font style="color:#969799; font-size: 1.1em;">Found ', len(foundAkk), ' entry</b> (within ', len(TSAEdata), ')</font><br>', unsafe_allow_html=True)
			else:
				with columas1:
					st.write('<b><font style="color:#969799; font-size: 1.1em;">Found ', len(foundAkk), ' entries</b> (within ', len(TSAEdata), ')</font><br>', unsafe_allow_html=True)
			with columas3:
				highlightAkk = st.checkbox('Highlight search terms', key='highlightAkk', value=True)

			if highlightAkk and akkAkkadian != '':
				akkAkkadian = r'(' + akkAkkadian + r')'
				foundAkk.loc[:, 'Term1'] = foundAkk['Term1'].apply(lambda x: re.sub(akkAkkadian, r'<span style="color:#05e6ff; font-weight: bold">\g<0></span>', x, flags=re.IGNORECASE))
			if highlightAkk and akkEnglish != '':
				akkEnglish = r'(' + akkEnglish + r')'
				foundAkk.loc[:, 'Meaning1'] = foundAkk['Meaning1'].apply(lambda x: re.sub(akkEnglish, r'<span style="color:#ff05ee; font-weight: bold">\g<0></span>', x, flags=re.IGNORECASE))				
			if highlightAkk and akkWrittenForm != '':
				akkWrittenForm = r'(' + akkWrittenForm + r')'
				foundAkk.loc[:, 'Written forms1'] = foundAkk['Written forms1'].apply(lambda x: re.sub(akkWrittenForm, r'<span style="color:#05ff50; font-weight: bold">\g<0></span>', x, flags=re.IGNORECASE))

			st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 3px solid #444;'>", unsafe_allow_html=True)
			st.write('<br>', unsafe_allow_html=True)
			for iA, akk_row in foundAkk.iterrows():
				with st.container():
					c1, c2, c3 = st.columns([5, 5, 5], gap='small')
					with c1:
						st.write(f'<b><i><font style="font-size: 1.2em; color: #ffffab;">{akk_row["Term1"]}</font></i></b></font>', unsafe_allow_html=True)
					with c2:
						st.write(f'<b><font style="font-size: 1.1em;">{akk_row["Written forms1"]}</font></b>', unsafe_allow_html=True)
					with c3:
						st.write(f'<b><font style="font-size: 1.1em;">{akk_row["Meaning1"]}</font></b>', unsafe_allow_html=True)
					if iA != foundAkk.index[-1]:
						st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 1px solid #444;'>", unsafe_allow_html=True)
		else:
			st.write('<br>', unsafe_allow_html=True)
			st.write('<p style="margin-bottom: 6em;"> </p>', unsafe_allow_html=True)
			st.write('<font style="color:#FF4B4B; font-size: 16px"><b>No entries found!</b></font>', unsafe_allow_html=True)
	else:
		st.write('<br>', unsafe_allow_html=True)
		st.write('<p style="margin-bottom: 6em;"> </p>', unsafe_allow_html=True)
		st.write('<font style="color:#FF4B4B; font-size: 16px"><b>Search fields are empty!</b></font>', unsafe_allow_html=True)

	st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 3px solid #444;'>", unsafe_allow_html=True)
	st.write('<br><font style="color: #969799;">Source file <b><i>gloss-akk.json</i></b> (part of <b><i>tsae.zip</i></b>). <a href="https://oracc.museum.upenn.edu/tsae/" target="_blank">TSAE: Textual Sources of the Assyrian Empire</a>. Available at https://oracc.museum.upenn.edu/json/tsae.zip.</font>', unsafe_allow_html=True)

######################################## SELECTED SIGN DETAILS AND PROTO-CUNEIFORM TAB ########################################
def splitCuneiformText(text):  # splits the text in a table containing both Latin and cuneiform characters for correction of the size in Sign details view
	if not text:
		return text
	if not re.search(r'[a-zA-Z]', text):
		return f'<span class="cuneiform-part">{text}</span>'
	parts = re.split(r'([a-zA-Z\s\/\-\.\,\(\)]+)', text)
	result = []
	for part in parts:
		if not part:
			continue
		if re.search(r'[a-zA-Z]', part):
			result.append(f'<span class="latin-part">{part}</span>')
		else:
			result.append(f'<span class="cuneiform-part">{part}</span>')
	return ''.join(result)

with st.container(border=True):
	if len(df1.columns) != 0:
		tabu1, tabu2 = st.tabs(['Sign details', 'Sumerian and Akkadian glossaries'])
		with tabu1:
			for index, row in df1.iterrows():
				st.write('<b><font style="font-size: 2em; color: #0AA43A;">', row['Name'], '</font></b>', unsafe_allow_html=True)
				c1, c2 = st.columns([7, 7], gap='small', border=True)
				with c1:
					st.subheader('Cuneiform')
					htmlCode = f"""
					<style>
						@media screen and (-webkit-min-device-pixel-ratio:0) {{
							::-webkit-scrollbar {{ width:6px; height:6px; }}
							::-webkit-scrollbar-thumb {{ background-color: rgba(180,180,180,0.4); border-radius:3px; }}
							::-webkit-scrollbar-track {{ background-color: rgba(0,0,0,0); }}
						}}
						table {{
							width: 100%;
							color: #ffffff;
							font-size: 0.95em;
							font-family: "Source Sans Pro", sans-serif;
							border-collapse: collapse;
							line-height: 1.75em;
						}}
						table td {{
							padding-top: 0.25cm;
							padding-bottom: 0.25cm;
							padding-left: 0.45cm;
						}}
						table tr {{
							border-bottom: 0.25px solid rgba(204, 204, 204, 0.2);
						}}
						table tr:last-child {{
							border-bottom: none;
						}}
						.cunei {{
							display: inline-block;
						}}
						.cuneiform-part {{
							display: inline-block;
							font-size: 30pt !important;
							vertical-align: middle;
						}}
						.latin-part {{
							display: inline-block;
							font-size: 1em !important;
							color: #969799;
							font-family: sans-serif !important;
							vertical-align: middle;
							line-height: 1.75em;
						}}
					</style>

					<table border="0">
						<tr><td width="40%"><b>Early Dynastic / Third millennium form:</b><br><font style="color: #969799;">– font <i>Oracc-LAK.ttf</i></font></td>
							<td width="60%"><span class="cunei" style="font-family: 'Oracc LAK'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>Early Dynastic IIIb form:</b><br><font style="color: #969799;">– font <i>Oracc-RSP.ttf</i></font></td>
							<td><span class="cunei" style="font-family: 'Oracc RSP'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>Gudea signs form:</b><br><font style="color: #969799;">– font <i>Oracc-gudea.ttf</i></font></td>
							<td><span class="cunei" style="font-family: 'Gudea'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>End of the 3<sup>rd</sup> millennium form:</b><br><font style="color: #969799;">– font <i>CuneiformComposite.ttf</i></font></td>
							<td><span class="cunei" style="font-family: 'CuneiformComposite'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>Old Babylonian monumental form:</b><br><font style="color: #969799;">– font <i>SantakkuM.ttf</i></font></td>
							<td><span class="cunei" style="font-family: 'SantakkuM'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>Old Babylonian literature form:</b><br><font style="color: #969799;">– font <i>OBFreie-Regular.ttf</i></font></td>
							<td><span class="cunei" style="font-family: 'OB Freie'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>Old Babylonian cursive form:</b><br><font style="color: #969799;">– font <i>Santakku.ttf</i></font></td>
							<td><span class="cunei" style="font-family: 'Santakku'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>Neo-Assyrian form:</b><br><font style="color: #969799;">– font <i>Assurbanipal.ttf</i></font></td>
							<td><span class="cunei" style="font-family: 'Assurbanipal'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>Neo-Assyrian form:</b><br><font style="color: #969799;">– font <i>Sinacherib.ttf</i></font></td>
							<td><span class="cunei" style="font-family: 'Sinacherib'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>Neo-Assyrian form:</b><br><font style="color: #969799;">– font <i>Nabuninuaihsus.ttf</i></font></td>
							<td><span class="cunei" style="font-family: 'Nabu-ninua-ihsus'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>Neo-Babylonian form:</b><br><font style="color: #969799;">– font <i>Esagil.ttf</i></font></td>
							<td><span class="cunei" style="font-family: 'Esagil'; color: #ffffab;">{splitCuneiformText(row['Sign'])}</span></td></tr>

						<tr><td><b>Values:</b></td><td>{row['Values1']}</td></tr>
						<tr><td><b>MesZL:</b></td><td>{row['MesZL']}</td></tr>
						<tr><td><b>ABZ/Labat:</b></td><td>{row['ABZ/Labat']}</td></tr>
						<tr><td><b>Unicode codepoint and name:</b></td><td>{row['Codepoint']}</td></tr>
					</table>

					<script>  // disable fallback glyphs and show empty space instead
					function supportsGlyph(font, char) {{
						const canvas = document.createElement('canvas');
						const ctx = canvas.getContext('2d');
						ctx.font = `30pt "${{font}}"`;
						const width1 = ctx.measureText(char).width;
						ctx.font = `30pt "monospace"`;
						const width2 = ctx.measureText(char).width;
						return width1 !== width2;
					}}

					// turn off fof Assurbanipal.ttf in Firefox (errors in the font, problems with thr visibility)
					const isFirefox = navigator.userAgent.toLowerCase().indexOf('firefox') > -1;

					for (const el of document.querySelectorAll('.cunei')) {{
						const char = el.textContent.trim();
						const font = window.getComputedStyle(el).fontFamily.replace(/["']/g, '');
						if (isFirefox && font === 'Assurbanipal') {{
							continue;
						}}
						if (!supportsGlyph(font, char)) {{
							el.textContent = '';
						}}
					}}
					</script>
					"""
					st.iframe(htmlCode, height="content")

					st.markdown("<hr style='margin: 0.2em 0; border: none; border-top: 3px solid #444;'>", unsafe_allow_html=True)
					st.markdown('<br>', unsafe_allow_html=True)

					with st.container():
						st.markdown('<b><font style="font-size: 1.3em;">Legend:</font></b>', unsafe_allow_html=True)
						st.markdown('<b>white</b> – values of MesZL<br><b><font color="#c5000b">dark-red</font></b> – values of Labat<br><b><font color="#579d1c">green</font></b> – values of ABZ<br><b><font color="#666666">gray</font></b> – commentaries', unsafe_allow_html=True)

			with c2:
				st.subheader('Proto-cuneiform')

				protoCunData = pd.read_csv('resources/signList/Proto-Cuneiform.csv', keep_default_na=False, na_values=[])

				searchSignProto = searchSignWithoutRegExp

				replacementsProto = {'Ḫ': 'H', 'ḫ': 'h'}

				selectedSign = str(row['Name'])

				for x,y in replacementsProto.items():
					selectedSign = selectedSign.replace(x, y)

				foundProtoCunDataSignName = protoCunData.loc[protoCunData['Name2'].str.contains('^' + selectedSign + '|\|' + selectedSign, case=False, regex=True)]  # by selected sign

				for x,y in replacementsProto.items():
					searchSignProto = searchSignProto.replace(x, y)
				foundProtoCunDataSearchTerm = protoCunData.loc[protoCunData['Name1'].str.contains('^' + searchSignProto + '|\|' + searchSignProto, case=False, regex=True)]  # by search string

				clu1, clu2 = st.columns([19, 15], gap='small')
				cl1, cl2, cl3, cl4, cl5 = st.columns([5, 10, 4, 5, 10], gap='small')

				if len(foundProtoCunDataSignName) != 0:
					n = 0
					with clu1:
						st.write('<br><b><i><font style="font-size: 1.2em">By selected sign name:</i> <font style="color: #ffffab;">', str(row['Name']), '</font></b>', unsafe_allow_html=True)
					for entry in range(len(foundProtoCunDataSignName)):
						with cl1:
							st.write('<b><font style="font-family: PCSL; font-size: 3.5em; color: #ffffab;">', foundProtoCunDataSignName['Sign'].iloc[n], '</font></b>', unsafe_allow_html=True)
						with cl2:
							st.write('<b><font style="font-size: 1.1em; line-height: 5.1em;">', foundProtoCunDataSignName['Name'].iloc[n], ' </font><font style="font-size: 1.1em; line-height: 5.1em; color: #969799;"> // code: ', foundProtoCunDataSignName['Code'].iloc[n], '</font> </b>', unsafe_allow_html=True)
						n = n+1

				if len(foundProtoCunDataSearchTerm) != 0 and str(searchSign) != '':
					m = 0
					with clu2:
						st.write('<br><b><i><font style="font-size: 1.2em">By search string:</i> <font style="color: #ffffab;">', searchSignOrigin, '</font></b>', unsafe_allow_html=True)
					for entry in range(len(foundProtoCunDataSearchTerm)):
						with cl4:
							st.write('<b><font style="font-family: PCSL; font-size: 3.5em; color: #ffffab;">', foundProtoCunDataSearchTerm['Sign'].iloc[m], '</font></b>', unsafe_allow_html=True)
						with cl5:
							st.write('<b><font style="font-size: 1.1em; line-height: 5.1em;">', foundProtoCunDataSearchTerm['Name'].iloc[m], '</font><font style="font-size: 1.1em; color: #969799;"> // code ', foundProtoCunDataSearchTerm['Code'].iloc[m], '</font></b>', unsafe_allow_html=True)
						m = m+1

				if len(foundProtoCunDataSearchTerm) == 0 and len(foundProtoCunDataSignName) == 0:					
					st.write('<font style="color: #FF4B4B; font-size: 16px"><b>Nothing found!</b></font>', unsafe_allow_html=True)

######################################## SUMERIAN AND AKKADIAN GLOSSARY TAB ########################################
		with tabu2:
			co1, co2 = st.columns([7, 7], gap='small', border=True)
			with co1:
				sumerianGlossary()
			with co2:
				akkadianGlossary()
	else:
		co1, co2 = st.columns([7, 7], gap='small', border=True)
		with co1:
			sumerianGlossary()
		with co2:
			akkadianGlossary()

st.divider()

######################################## SOURCES AND REFERENCES ########################################
st.write('<b><font style="font-size: 29px">Sources and references', unsafe_allow_html=True)

with st.expander('', expanded=False):
	#st.markdown('<b><font style="font-size: 1.3em;">Sources:</font></b>', unsafe_allow_html=True)
	st.markdown('**Fonts**', unsafe_allow_html=True)
	st.markdown(
		'– *PCSL.ttf* (by A. Pandey and S. Tinney). https://oracc.museum.upenn.edu/osl/OraccCuneiformFonts/index.html and https://github.com/oracc/oracc2/tree/main/msc/fonts.<br>'
		'– *Oracc-LAK.ttf* (by S. Tinney and V. Kethana). https://oracc.museum.upenn.edu/osl/OraccCuneiformFonts/index.html and https://github.com/oracc/oracc2/tree/main/msc/fonts.<br>'
		'– *Oracc-RSP.ttf* (by S. Tinney). https://oracc.museum.upenn.edu/osl/OraccCuneiformFonts/index.html and https://github.com/oracc/oracc2/tree/main/msc/fonts.<br>'
		'– *Oracc-gudea.ttf* (by S. Tinney). https://oracc.museum.upenn.edu/osl/OraccCuneiformFonts/index.html and https://github.com/oracc/oracc2/tree/main/msc/fonts.<br>'
		'– *CuneiformComposite.ttf* (by S. Tinney). http://oracc.museum.upenn.edu/doc/help/visitingoracc/fonts/.<br>'
		'– *SantakkuM.ttf* (by S. Vanséveren). https://www.hethport.uni-wuerzburg.de/cuneifont/.<br>'
		'– *Old Babylonian Freie* (by C. R. Ziegeler). https://refubium.fu-berlin.de/handle/fub188/45271 and https://github.com/crzfub/OB-Freie.<br>'
		'– *Santakku.ttf* (by S. Vanséveren). https://www.hethport.uni-wuerzburg.de/cuneifont/.<br>'
		'– *Assurbanipal.ttf* (by S. Vanséveren). https://www.hethport.uni-wuerzburg.de/cuneifont/.<br>'
		'– *Nabuninuaihsus.ttf* (by R. Leroy). https://github.com/eggrobin/Nabu-ninua-ihsus, https://oracc.museum.upenn.edu/osl/OraccCuneiformFonts/index.html and https://github.com/oracc/oracc2/tree/main/msc/fonts.<br>'
		'– *Sinacherib.ttf* (by K. Šašková). http://home.zcu.cz/~ksaskova/.<br>'
		'– *Esagil.ttf* (by S. Vanséveren). https://www.hethport.uni-wuerzburg.de/cuneifont/.', unsafe_allow_html=True)
	st.markdown('**Glossaries and dictionaries**', unsafe_allow_html=True)
	st.markdown('– Sumerian: <b><i>gloss-sux.json</i></b> (part of <b><i>epsd2.zip</i></b>). https://oracc.museum.upenn.edu/epsd2/JSON/index.html.<br>'
		'&ensp; &ensp; ‣ the glossary of *The Pennsylvania Sumerian Dictionary Project 2* (ePSD2). Philadelphia: University of Pennsylvania Museum of Anthropology and Archaeology. http://psd.museum.upenn.edu/nepsd-frame.html.<br>'
		'– Akkadian: <b><i>gloss-akk.json</i></b> (part of <b><i>tsae.zip</i></b>). https://oracc.museum.upenn.edu/json/tsae.zip.<br>'
		'&ensp; &ensp; ‣ the glossary of the *Textual Sources of the Assyrian Empire* (TSAE). Philadelphia: The Open Richly Annotated Cuneiform Corpus. https://oracc.museum.upenn.edu/tsae/.', unsafe_allow_html=True)
	st.markdown('**Sign lists**', unsafe_allow_html=True)
	st.markdown(
		'– Borger, R. (2004): *Mesopotamisches Zeichenlexikon* (AOAT 305). Münster: Ugarit-Verlag.<br>'
		'– Borger, R. (1981): *Assyrisch-babylonische Zeichenliste* (AOAT 1981). Neukirchen-Vluyn.<br>'
		'– Labat, R. (1994): *Manuel d’épigraphie akkadienne*. Paris.<br>'
		'– Tinney, S. et al. (2017–): *ePSD2 Sign List*. The Pennsylvania Sumerian Dictionary Project 2 (ePSD2). Philadelphia: University of Pennsylvania Museum of Anthropology and Archaeology. https://oracc.museum.upenn.edu/epsd2/signlist/.<br>'
		'– Veldhuis, N., Tinney, S. et al. (2014–): *OSL: Oracc Sign List*. Philadelphia: The Open Richly Annotated Cuneiform Corpus. https://oracc.museum.upenn.edu/osl/.<br>'
		'– *PCSL: Proto-Cuneiform Sign List*. Philadelphia: The Open Richly Annotated Cuneiform Corpus. https://oracc.museum.upenn.edu/pcsl/.<br>'
		'– *eBL: Signs*. electronic Babylonian Library (eBL). München: Ludwig-Maximilians-Universität München – Bayerische Akademie der Wissenschaften. https://www.ebl.uni-muenchen.de/signs.<br>'
		'– Šašková, K. (2021): <i>Cuneiform Sign Llist</i>. https://home.zcu.cz/~ksaskova/Sign_List.html.<br>'
		'– <i>Catalogue of Old Babylonian Signs</i>. Old Babylonian Text Corpus (OBTC). Pilsen: University of West Bohemia. https://klinopis.zcu.cz/utf/signs.html.', unsafe_allow_html=True)
	st.markdown('**Tools**', unsafe_allow_html=True)
	st.markdown('– Cuneify REPL (by Jon Knowles). https://amazing-chandrasekhar-e6c92b.netlify.app/index.html.<br>'
		'– CuneifyPlus (by Tom Gillam). https://cuneify.herokuapp.com/.<br>'
		'– Cuneify (by Andrew Senior). https://andrewsenior.com/cuneify/index.html and https://github.com/asenior/cuneify.<br>'
		'– Cuneify (by Steve Tinney). http://oracc.museum.upenn.edu/saao/knpp/cuneiformrevealed/cuneify/.<br>'
		'– CuneifyTool (by K. Šašková). https://cuneifytool.streamlit.app/.<br>'
		'– eBL: Cuneiform converter. electronic Babylonian Library (eBL). München: Ludwig-Maximilians-Universität München – Bayerische Akademie der Wissenschaften. https://www.ebl.uni-muenchen.de/tools/cuneiform-converter.<br>'
		'– KUR.NU.GI4.A – Cuneiform Script Analyzer (by uyum). https://kurnugia.web.app/.<br>'
		'– GI-DUB – Sumerian Cuneiform Input Aid (by uyum). https://qantuppi.web.app/.', unsafe_allow_html=True)

######################################## FOOTER ########################################
st.write('<br><br>', unsafe_allow_html=True)

footer = """<style>
.footer a:link, .footer a:visited {
color: #575656;
text-decoration: none;
}

.footer a:hover, .footer a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: #0e1117;
text-align: left;
z-index: 9999;
font-size: 1.2em;
color: #575656;
padding: 2px 0px 2px 1rem;
}

.footer p {
margin: 0;
padding: 0;
}
</style>
<div class="footer">
<p><a href="https://zcu.academia.edu/Kate%C5%99ina%C5%A0a%C5%A1kov%C3%A1" target="_blank">KacaSas</a> 2026</p>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
