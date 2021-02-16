from urllib import response

import imaplib, email, os
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('username')
password = os.getenv('password')


def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)


imap = imaplib.IMAP4_SSL('imap.gmail.com')
imap.login(username, password)
imap.select('"Bible_Project"')

res, data = imap.uid('search', None, 'ALL')
messages = data[0].split()
res, msg = imap.fetch(messages[0], "(RFC822)")

success = False
print(msg)
for response in msg:
    if isinstance(response, tuple):
        print("test")
        # parse a bytes email into a message object
        msg = email.message_from_bytes(response[1])
        # decode the email subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            # if it's a bytes, decode to str
            subject = subject.decode(encoding)

        subject = subject[subject.find("Week "):subject.find("Week ") +
                          7].rstrip()
        choppedSubject = subject.replace(' ', '-').lower()
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
# close the connection and logout
imap.close()
imap.logout()

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
