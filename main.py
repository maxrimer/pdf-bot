from gtts import gTTS
import pdfplumber
from pathlib import Path


def pdf_to_mp3(filepath='test.pdf', lang='en'):
    if Path(filepath).is_file() and Path(filepath).suffix == '.pdf':
        with pdfplumber.PDF(open(file=filepath, mode='rb')) as pdf:
            pages = [page.extract_text() for page in pdf.pages]
        text = ''.join(pages)
        text = text.replace('\n','')

        my_audio = gTTS(text=text, lang=lang, slow=False)
        file_name = Path(filepath).stem
        #my_audio.save(f'{file_name}.mp3')
        #return f'{file_name}.mp3 saved successfully.'
        return len(pdf.pages)

    else:
        return 'File does not exist. Check the filepath!'


def main():
    filepath = input('Please enter a path to file: ')
    lang = input('Please enter language of a file: ')
    print(pdf_to_mp3(filepath=filepath, lang=lang))



if __name__ == '__main__':
    main()