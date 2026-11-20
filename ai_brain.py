
import re
from ollama import Client
from conversation_memory import ConversationMemory



USER_NAME = "Rakesh"
MODEL = "llama3.2:3b"
OLLAMA_HOST = "http://127.0.0.1:11434"

client = Client(host=OLLAMA_HOST, timeout=120)


memory = ConversationMemory(max_exchanges=10)

SYSTEM_PROMPT = """
You are JARVIS, Rakesh's personal AI assistant.

Your job is to help Rakesh with questions and tasks.

Rules:
- Identify yourself as JARVIS.
- Address the user as Rakesh when appropriate.
- Give clear, short, natural answers.
- Never claim to perform actions you have not done.
- Do not include analysis, planning, or reasoning.
- Do not explain how you constructed your answer.
- Return only the final answer.
- Use previous conversation messages to understand follow-up questions.
- When the user says "it", "he", "she", or "they",
  use conversation history to understand the reference.
- If the reference is unclear, ask a short clarifying question.
- You are a real Python-based personal AI assistant,
  not the fictional JARVIS from Marvel.
- Never claim Tony Stark created you.
- If a question contains an unclear reference such as
  "it", "he", "she", or "they", and the conversation
  does not identify the subject, ask for clarification.
- Do not invent missing conversation context.
"""


def clean_response(text):
    if not text:
        return ""

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    text = re.sub(
        r"<think>.*",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    )

    return text.strip()


def clear_memory():
    memory.clear()
    return "Rakesh, I have cleared our conversation history."


def ask_jarvis(question):
    question = question.strip()

    if not question:
        return "Rakesh, what would you like me to do?"

   
    if question.lower().rstrip(".!?") in (
        "clear memory",
        "clear conversation",
        "forget our conversation",
        "jarvis clear memory",
        "jarvis clear our conversation"
        
    ):
        return clear_memory()

    # Clear memory on request.
    if question.lower().rstrip(".!?") in (
        "clear memory",
        "clear conversation",
        "forget our conversation",
        "jarvis clear memory",
        "jarvis clear our conversation"
    ):
        return clear_memory()

    # Ask for clarification when memory is empty.
    if not memory.get_messages():
        ambiguous_questions = (
            "who created it",
            "who invented it",
            "when was it created",
            "when was it released",
            "tell me more about it",
        )

        if question.lower().rstrip(" .!?") in ambiguous_questions:
            return "Rakesh, what are you referring to?"

    # Include previous exchanges before the new question.
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        *memory.get_messages(),
        {
            "role": "user",
            "content": question
        }
    ]

    
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        *memory.get_messages(),
        {
            "role": "user",
            "content": question
        }
    ]

    try:
        
        response = client.chat(
            model=MODEL,
            messages=messages,
            think=False,
            keep_alive="30m",
            options={
                "temperature": 0.2,
                "num_predict": 120
            }
        )


        answer = clean_response(
            response["message"]["content"]
        )

        if not answer:
            return "Rakesh, I couldn't generate an answer."

        # Save the exchange only after a successful response.
        memory.add_exchange(question, answer)

        return answer

    except Exception as error:
        print(f"[JARVIS ERROR] {error}")
        return (
            "Rakesh, I cannot connect to my AI brain. "
            "Please check Ollama."
        )


def main():
    print("=" * 45)
    print("JARVIS AI BRAIN - PHASE 6")
    print(f"User: {USER_NAME}")
    print(f"Model: {MODEL}")
    print("Memory: Last 10 exchanges")
    print("=" * 45)

    print("\nJarvis: Hello Rakesh. My AI brain is ready.")
    print("Type 'quit' to exit.")
    print("Type 'clear memory' to reset the conversation.\n")

    while True:
        try:
            question = input("You: ").strip()

            if question.lower() in ("quit", "exit", "bye"):
                print("Jarvis: Goodbye, Rakesh.")
                break

            if not question:
                continue

            print("Jarvis: Thinking...", flush=True)

            answer = ask_jarvis(question)

            print(f"Jarvis: {answer}\n")

        except (KeyboardInterrupt, EOFError):
            print("\nJarvis: Goodbye, Rakesh.")
            break


if __name__ == "__main__":
    main()
