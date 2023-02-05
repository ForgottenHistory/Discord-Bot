import random
def check_response_text(prompt, response_text, previous_response, char_name, memory):
    default_responses = [
    "I'm not sure what you mean.",
    "Can you please clarify?",
    "Can you rephrase the question?",
    "Sorry, I didn't understand that."
    ]
    
    # Check if response text is not correct
    # Sends a default response if no
    if response_text == "":
        response_text = random.choice(default_responses)
    elif response_text == prompt:
        response_text = random.choice(default_responses)
    elif response_text == previous_response:
        response_text = random.choice(default_responses)
    else:
        memory.append(f"{char_name}: " + response_text)
