import streamlit as st
import google.generativeai as genai
import re
import os
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from googletrans import Translator

#loading environment variables and configuring gemini api
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

#for extractin video id from youtube url
def extract_video_id(youtube_url):
    # Regular expression pattern to match the video code
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, youtube_url)
    
    if match:
        return match.group(1)
    else:
        return None
    
#translating summary 
def translate_summary(summary, target_language):
    translator = Translator() 
    translated = translator.translate(summary, dest=target_language) 
    return translated.text.replace("**", "")

#for getting transcript  
def extract_transcript_details(video_id):
    try:
        if video_id:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[
            "en", "hi", "bn", "ta", "te", "kn", "ml", "as", "or", "gu", "mr", "ne", "pa", 
            "sd", "si","ab", "aa", "af", "ak", "sq", "am", "ar", "hy", "ay", "az", "ba", "eu", "be", "bho",
            "bs", "br", "bg", "my", "ca", "ceb", "zh-Hans", "zh-Hant", "co", "hr", "cs", "da",
            "dv", "nl", "dz", "eo", "et", "ee", "fo", "fj", "fil", "fi", "fr", "gaa", "gl", "lg",
            "ka", "de", "el", "gn", "ht", "ha", "haw", "iw", "hmn", "hu", "is", "ig", "id",
            "ga", "it", "ja", "jv", "kl", "kk", "kha", "km", "rw", "ko", "kri", "ku", "ky", "lo",
            "la", "lv", "ln", "lt", "luo", "lb", "mk", "mg", "ms", "mt", "gv", "mi", "mr", "mn",
            "mfe", "new", "nso", "no", "ny", "oc", "om", "os", "pam", "ps", "fa", "pl", "pt",
            "pt-PT", "qu", "ro", "rn", "ru", "sm", "sg", "sa", "gd", "sr", "crs", "sn", "sd",
            "si", "sk", "sl", "so", "st", "es", "su", "sw", "ss", "sv", "tg", "tt", "th",
            "bo", "ti", "to", "ts", "tn", "tum", "tr", "tk", "uk", "ur", "ug", "uz", "ve", "vi",
            "war", "cy", "fy", "wo", "xh", "yi", "yo", "zu"
            ]) 
            last_entry = transcript[-1]
            duration = (last_entry["start"] + last_entry["duration"])//60
            st.write(f"Video Duration: {duration} minutes")
            transcript_text = ""
            for i in transcript:
                transcript_text += " " + i["text"]
            print(transcript_text)
            return transcript_text,duration
        else:
            st.error( "Video ID not found in the provided URL Pleas Provide Correct URL.")
    except Exception as e:
        st.error("transcript"+e)

#for extracting summary from transcription using gemini api
def generate_gemini_content(transcript_text,prompt):
    try:
        model=genai.GenerativeModel("gemini-2.5-flash-lite")
        response=model.generate_content(prompt+transcript_text)
        return response.text
    except Exception as e:
        st.error("gemini"+e)

def calculate_summary_words(duration, summary_type):
    if summary_type == "Short Summary":
        factor = 3
    elif summary_type == "Medium Summary":
        factor = 6
    else:
        factor = 12
    words=duration * factor
    if words < 50:  # minimum words
        words = 50
    st.write(f"Generating a summary of approximately {words} words.")
    return int(words)

#frontend interface using streamlit
st.markdown("<h1 style='text-align: left; color: #FF6347;'> YouTube Video Summarizer</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: left; color: white;'>This will work well only if the youtube video has a good transcription</h5>", unsafe_allow_html=True)

youtube_link = st.text_input("Paste or enter YouTube video link:")
target_language=st.text_input("Enter you prefered language code(e.g. 'hi' for hindi, 'te' for telugu, 'es' for spanish, search in google if you don't know) ")
summary_type = st.selectbox("Choose summary type:", ["Short Summary", "Medium Summary", "Long Summary"])
if youtube_link:
    video_id = extract_video_id(youtube_link)
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", width="stretch")

if st.button("Get Detailed Notes"):
    if youtube_link:
        try:
            transcript_text,duration = extract_transcript_details(video_id)
            words=calculate_summary_words(duration, summary_type)
            prompt = f"""
You are a specialized YouTube video summarizer. Your task is to take the provided transcript text and generate a comprehensive, accurate summary. The summary length should be approximately {words} words, but it must NEVER exceed 3500 characters in total. Avoid unnecessary elaboration or repetition.

Instructions:
- The transcript may be in any language; you must understand it and provide the output in English only.
- Title: Include the video title at the top.
- Intro Summary: Provide a brief overview.
- Detailed Summary: Use concise bullet points for key information and transitions.
- Subtopics: Use short headings and group related content under them.
- Key Takeaways: End with a short, actionable list of 3–5 takeaways.
- Avoid over-explaining, repeating, or adding filler words.
- The ENTIRE OUTPUT must be strictly under 3500 characters, even if {words} words were requested.

Here is the transcript:
"""
            if transcript_text:
                if target_language:
                    if target_language!='en':
                        summary = generate_gemini_content(transcript_text,prompt)
                        summary=translate_summary(summary, target_language)
                    else:
                        summary = generate_gemini_content(transcript_text, prompt)
                else:
                    summary = generate_gemini_content(transcript_text, prompt)
                st.markdown("<h2 style='color: #FF6347;'>Detailed Notes:</h2>", unsafe_allow_html=True)
                st.write(summary)
        except Exception as e:
            st.error("An error occurred:")
            st.error("unknown"+str(e))
            st.error("Sorry, we couldn't retrieve the transcript for this video. It might not be available or there could be an issue with the connection.")
    else:
        st.error("Please enter a valid YouTube video link.")
            
