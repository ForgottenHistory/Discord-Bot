import re

def reformat_chat_logs(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        chat_logs = f.read()
    
    # Use regular expression to match the username and message
    pattern = r"(\w+#\d{4}): (.*)"
    matches = re.finditer(pattern, chat_logs)
    reformatted_text = ""

    for match in matches:
        username = match.group(1)
        message = match.group(2)
        username = re.sub(r'#[0-9]+', '', username)
        message = re.sub(r'<[A-Za-z0-9_:]+>', '', message)
        #message = re.sub(r'<:[A-Za-z0-9_]+:[0-9]+>', '', message)
        #message = re.sub(r'<a:[A-Za-z0-9_]+:[0-9]+>', '', message)
        if message.strip() and not message.startswith("http"):
            reformatted_text += f"{username}: {message}\n"

    return reformatted_text

print("Converting...")
reformatted_text = reformat_chat_logs("./dataset/chatlog.txt")
reformatted_text = reformatted_text.replace("@","")
with open("./dataset/reformatted_text.txt", "w", encoding='utf-8') as f:
    f.write(reformatted_text)
