import openai
import time
import asyncio
import pyttsx3
from gtts import gTTS
import os
openai.api_key = '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'
# openai.api_key = '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' # key name: masterthesis_testkey, See: https://platform.openai.com/account/api-keys
model_engine = "text-davinci-003"


def change_voice(engine, language):
    # language  : Microsoft Hedda Desktop - German, Microsoft Zira Desktop - English (United States), Microsoft Helena Desktop - Spanish (Spain), ... en_US, de_DE, ...
    # gender    : VoiceGenderFemale, VoiceGenderMale
    # age       : 
    language = str(language)
    for voice in engine.getProperty('voices'):
        if language in voice.name: #and gender == voice.gender:
            engine.setProperty('voice', voice.id)
            return True

    raise RuntimeError("Language '{}' for gender '{}' not found".format(language))

async def ask_chatgpt(read_loud=False, voice_language='en' ,text_file_name='openai_output.py', user_prompt: str = None, remote: bool = False) -> str:
    #voice_language : 'en' - english, 'de' - deutsch, 'es' - español
    try:
        system_languages = {
            'en': 'Microsoft Zira Desktop - English (United States)',
            'de': 'Microsoft Hedda Desktop - German',
            'es': 'Microsoft Helena Desktop - Spanish (Spain)',
        }

        if user_prompt == None:
            user_prompt = input("Ask ChatGPT: ")

        start = time.time()

        completion = openai.Completion.create(
            engine = model_engine,
            prompt = user_prompt,
            max_tokens = 1024,
            n = 1,
            stop = None,
            temperature = 0.5,
            )
        response = completion.choices[0].text
        end = time.time()
        print(f'ChatGPT ({model_engine}) response at {time.strftime("%d.%m.%Y %H:%M:%S")}: \n<<<{response}\n\n>>>\nresponse took: {end-start} (sec)')
        
        if read_loud:
            text_speech = pyttsx3.init()
            change_voice(text_speech,system_languages.get(voice_language))
            text_speech.say(response)
            text_speech.runAndWait()
            # print(type(response))
            # spoken = gTTS(text=response, lang='en', slow=False)
            # spoken.save("spoken.mp3")
            # time.sleep(5)
            # os.system("mpg321 spoken.mp3")
        if remote == False:
            saving = input(f"save text answer as file '{text_file_name}'? (y/n) ")
            if saving.lower() == "y":
                with open(text_file_name,'w') as file:
                    file.writelines(response)
        return str(response)
    except KeyboardInterrupt:
        raise Exception('KeyboardInterrupt: user killed the chat GPT API script')

async def main():
    await ask_chatgpt(read_loud=True,voice_language="en",text_file_name='openai_output.py')

if __name__ == '__main__':
    asyncio.run(main())
