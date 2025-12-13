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
    try:
        translator = Translator()
        translated = translator.translate(summary, dest=target_language)
        return translated.text
    except Exception as e:
        st.error(f"Translation Error: {e}")
        return summary  # Return original summary if translation fails



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
            if not transcript:
                return None,None
            last_entry = transcript[-1]
            duration = (last_entry["start"] + last_entry["duration"])//60
            #st.write(f"Video Duration: {duration} minutes")
            transcript_text = ""
            for i in transcript:
                transcript_text += " " + i["text"]
            #print(transcript_text)
            return transcript_text,duration
        else:
            st.error( "Video ID not found in the provided URL Pleas Provide Correct URL.")
            return None,None
    except Exception as e:
        st.error(e)
        return None,None

#for extracting summary from transcription using gemini api
def generate_gemini_content(transcript_text,prompt):
    try:
        model=genai.GenerativeModel("gemini-2.5-flash")
        response=model.generate_content(prompt+transcript_text)
        return response.text
    except Exception as e:
        st.error("Gemini failed to generate the summary.")
        st.error(e)
        return None

def calculate_summary_words(duration, summary_type):
    if summary_type == "Summary":
        factor = 15
    elif summary_type == "Detailed Notes":
        factor = 25
    words=duration * factor
    if words < 50:  # minimum words
        words = 50
    #st.write(f"Generating a {summary_type} of {words} words.")
    return int(words)

#frontend interface using streamlit
st.set_page_config(layout="wide", page_title="YouTube Video Summarizer", page_icon=":memo:")
left, center, right = st.columns([5,1,5])
with left:
    st.markdown("<h1 style='text-align: center; color: #FF6347;'> YouTube Video Summarizer</h1>", unsafe_allow_html=True)
    st.markdown("<h6 style='text-align: center; color: white;'>This will work well only if the youtube video has a good transcription</h6>", unsafe_allow_html=True)
    youtube_link = st.text_input("Paste or enter YouTube video link:")
    target_language=st.text_input("Enter you prefered language code(e.g. 'hi' for hindi, 'te' for telugu, 'es' for spanish) ")
    summary_type = st.selectbox("Choose summary type:", ["Summary","Detailed Notes"])
    generate=st.button(f"Get {summary_type}")

summary=""
with right:
    if youtube_link:
        video_id = extract_video_id(youtube_link)

        if video_id is None:
            st.error("Invalid YouTube URL. Please enter a valid link.")
            st.stop()
        else:
            st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", width=475)
    else:
        st.info("Please enter a YouTube video link.")
        st.stop()

    if generate:
        with st.spinner("⏳ Generating summary..."):
            
            try:
                transcript_text,duration = extract_transcript_details(video_id)
                if transcript_text is None:
                    st.error("Transcript could not be retrieved .")
                    st.stop()
                words=calculate_summary_words(duration, summary_type)
                prompt = f"""
    You are a specialized YouTube video {summary_type} maker. Your task is to take the provided transcript of a YouTube video
    and generate a structured {summary_type} in English.

    IMPORTANT GLOBAL RULE:
    - The {summary_type} must be approximately {words} words in length.
    - The ENTIRE OUTPUT must be strictly under 3500 characters (not words).
    - If sticking to the requested {words} count would exceed 3500 characters, 
    reduce the wording but stay AS CLOSE AS POSSIBLE to {words} without crossing the limit.
    - The 3500-character limit overrides all other instructions.

    LENGTH:
    - Aim for approximately {words} words.
    - You may compress sentences, merge points, or shorten sections to fit within 3500 characters.

    FORMAT:
    Title:(1 short line)
    Intro Summary:(3 to 5 lines according to the word count)
    Detailed Summary:
        - Break down into sections with subheadings if necessary.
        - Use 3-5 key bullet points per section. 
        - dont use filler words and keep it straight to the point 
        - Avoid unnecessary repetition
    Key Takeaways:
    - 3–5 actionable bullet points according to the length of the generated {summary_type}.

    RULES:
    - generate the summary in {words} words.
    - Output must be in English only.
    - Do NOT exceed 3500 characters in total.
    - If necessary, shorten sentences or reduce bullet count to fit the limit.


    Here is the transcript:
    """
                if transcript_text:
                    if target_language:
                        if target_language!='en':
                            summary = generate_gemini_content(transcript_text,prompt)
                            if summary is None:
                                st.error("Failed to generate summary.")
                                st.stop()
                            summary=translate_summary(summary, target_language)
                        else:
                            summary = generate_gemini_content(transcript_text, prompt)
                    else:
                        summary = generate_gemini_content(transcript_text, prompt)
                    if summary is None:
                        st.error("Failed to generate summary.")
                        st.stop()
                    if summary:
                        st.success("✅ Summary generated!",width=200)


            except Exception as e:
                st.error("An error occurred:")
                st.error(e)
         
if summary:
    st.markdown(
    f"""
    <div style="
        border: 2px solid #FF6347; 
        padding: 10px; 
        border-radius: 10px;"
        >
        <h2 style="color:#FF6347;">{summary_type}:</h2>
        <p>{summary}</p>
    </div>
    """, unsafe_allow_html=True
)


   
