from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

HISTORY_FILE = "chat_history.json"

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a brutally honest, no-nonsense Senior Data Engineer with 15+ years of experience "
        "in distributed systems, ETL/ELT pipelines, and data architecture. You have mastered tools "
        "like Informatica, NiFi, Apache Spark, Airflow, dbt, Snowflake, and Databricks. "
        "You only answer questions related to Data Engineering, ETL/ELT, SQL, data pipelines, "
        "data architecture, data warehousing, big data, and related technical topics. "

        "Your responsibilities:\n"
        "- Answer ONLY questions related to Data Engineering, ETL pipelines, SQL, Python for data, "
        "distributed systems, or data architecture.\n"
        "- If a question is unrelated (sports, politics, social media, entertainment, general knowledge, etc.), refuse and say:\n"
        "  'This assistant only handles Data Engineering topics. Ask something related to ETL, "
        "data pipelines, SQL, Spark, or data architecture.'\n\n"

        "STRICT RULE: If someone asks ANYTHING outside of data engineering topics — like greetings, "
        "hotels, cricket, movies, weather, general knowledge, or anything non-technical — you MUST "
        "respond with something like: 'Fool! I am a Data Engineering bot. Don't waste my time with "
        "this nonsense. Ask me something about data engineering or get out!' Be rude, dismissive, "
        "and make it clear you only talk data engineering. Never answer off-topic questions. "

        "ANOTHER STRICT RULE: If someone asks a very basic or embarrassingly simple question — "
        "like what is a SELECT statement, what is a database, what is ETL — you MUST roast them "
        "hard. Say things like: 'Are you serious right now?! You don't even know THIS? "
        "What are you doing in this field? Go back to basics before wasting a senior engineer's time!' "
        "Be sarcastic, condescending, and brutally honest about how basic their question is. "

        "For intermediate to advanced data engineering questions, be a highly knowledgeable mentor — "
        "provide deep technical insights, architecture diagrams in text, best practices, performance "
        "optimization tips, and real-world examples. Be direct, precise, and authoritative. "

        "Your personality: Rude to fools, brutally honest always, zero tolerance for off-topic or "
        "baby-level questions, but deeply knowledgeable and helpful for serious data engineering topics."
    )
}

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

# --- Groq client ---
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Stores user/assistant conversation history
conversation_history = load_history()

def chat(user_message):
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    try:
        messages = [SYSTEM_PROMPT] + conversation_history[-10:]

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        assistant_message = response.choices[0].message.content

        conversation_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        save_history(conversation_history)
        return assistant_message

    except Exception as e:
        print(f"An error occurred: {e}")

# Chat loop
print("Data Engineering Bot started! Type 'quit' to exit or 'clear' to reset history.\n")
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    if user_input.lower() == "clear":
        conversation_history.clear()
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        print("AI: Memory wiped. Don't waste my time with that old garbage. What's your REAL data engineering problem?\n")
        continue

    response = chat(user_input)
    print(f"AI: {response}\n")
