import re

def reformat_chat_logs(file_path):
    with open(file_path, "r", encoding='utf-8') as file:
        text = file.read()
        # Use regular expressions to extract the username and message
        matches = re.finditer(r"\[.*\] ([A-Za-z0-9#]+)[^\n]*\n(.*)", text)
        reformatted_text = ""
        for match in matches:
            username = match.group(1)
            # remove the tag from the username
            username = re.sub(r"([A-Za-z]+)#[0-9]{4}", r"\1", username)
            message = match.group(2)
            # remove links from message
            message = re.sub(r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?", "", message)
            #text = re.sub(r'<:[A-Za-z0-9_]+:[0-9]+>', '', message)
            print(text)
            # remove empty messages
            if message.strip() != "":
                reformatted_text += f"{username}: {message}\n"
    return reformatted_text


reformatted_text = reformat_chat_logs("./dataset/chatlog.txt")
reformatted_text = reformatted_text.replace("[ AM ]", "").replace("[ PM ]", "").replace("@","")
with open("./dataset/reformatted_text.txt", "w", encoding='utf-8') as f:
    f.write(reformatted_text)
