from urllib import response

import imaplib, email, os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('username')
password = os.getenv('password')


def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)


imap = imaplib.IMAP4_SSL('imap.gmail.com')
imap.login(username, password)
status, messages = imap.select('"Bible_Project"')

num_of_messages = int(messages[0])
print(num_of_messages)
# N is start M is stop

# gets the latest email
N = num_of_messages-1 # start 1
M = num_of_messages   # stop 0

single = True

success = False
for i in range(num_of_messages-N, num_of_messages-M, -1):
    if single:
        res, msg = imap.fetch(messages[0], "(RFC822)")
    else:
        res, msg = imap.fetch(str(i), "(RFC822)")
    success = False
    for response in msg:
        if isinstance(response, tuple):
            # parse a bytes email into a message object
            msg = email.message_from_bytes(response[1])
            subject = msg["Subject"]
            print(subject)
            subject = subject[subject.find("Week "):subject.find("Week ") +7].rstrip()
            choppedSubject = subject.replace(' ', '-').lower()
            print(subject)
            # if the email message is multipart
            if msg.is_multipart():
                # iterate over email parts
                for part in msg.walk():
                    # extract content type of email
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    try:
                        # get the email body
                        body = part.get_payload(decode=True).decode()
                    except:
                        pass
                    if "attachment" in content_disposition:
                        # download attachment
                        print("Downloading attachments")
                        filename = part.get_filename()
                        if filename:
                            folder_name = clean(subject)
                            if not os.path.isdir(folder_name):
                                # make a folder for this email (named after the subject)
                                os.mkdir(folder_name)
                            filepath = os.path.join(folder_name, filename)
                            # download attachment and save it
                            open(filepath,
                                "wb").write(part.get_payload(decode=True))
                print("fetched")
            else:
                # extract content type of email
                content_type = msg.get_content_type()
                # get the email body
                body = msg.get_payload(decode=True).decode()
            
                print("fetched")

            body = body.replace("http:", "https:")

            if content_type == "text/html":
                filename = "public/" + choppedSubject + ".html"
                # write the file
                pos = body.find("</head>")
                
                with open(filename, "w") as f:
                    f.writelines(body[:pos])
                    f.writelines(
                        '<style> body { background-color: #192f57; } #back { text-decoration: none; color: white; position: fixed; top: 30px; left: 30px; }</style>\n')
                    f.writelines("</head>\n")
                    f.writelines('<a id="back" href="/">BACK</a>\n')
                    f.writelines(body[pos+9:])
                    success = True
                    print("file created")


    if success:
        success = False
        with open('public/index.html', 'r') as file:
            # read a list of lines into data
            data = file.readlines()
            print("reading index.html")
        # get position of last week
        index = data.index("            <!-- endOfWeeks -->\n")
        div = '            <a href="/' + choppedSubject + '.html">' + subject + '</a>\n'
        data.insert(index, div)
        
        print("insterted code")

        with open('public/index.html.tmp', "w") as f:
            f.writelines("%s" % place for place in data)
            success = True
            print("written temp")

    if success:
        os.rename('public/index.html.tmp', 'public/index.html')
    print("re-write complete")

# close the connection and logout
imap.close()
imap.logout()

# Must alreday be singed into firebase and git
os.chdir('/media/bray/Mass Storage/Coding Projects/BibleProject')
os.system("firebase deploy")

os.system("git add .")
os.system('git commit -m "' + subject + '"')
os.system("git push")